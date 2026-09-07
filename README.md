# mcp-huawei-cloud

MCP servers para Huawei Cloud, listos para descargar e integrar.

| MCP | Puerto | Transporte | Qué hace |
|-----|--------|-----------|----------|
| **hwc-ops-bss** | `8888` | streamable HTTP `/mcp` | Ops read-only (ECS/VPC/OBS/IAM/ELB/EVS/CES/CTS/DNS/LTS/CBR) + BSS billing/cost |
| **terraform-mcp** | `8088` | streamable HTTP `/mcp` | Lookups contra el Terraform Registry (módulos, providers, versiones) |

## Setup rápido

```bash
cp .env.example .env          # completar AK/SK (o dejar vacío en modo multi-tenant)
docker compose up -d --build
```

Verificar:

```bash
curl -s http://localhost:8888/mcp   # hwc-ops-bss
curl -s http://localhost:8088/mcp   # terraform-mcp
```

## hwc-ops-bss (autocontenido)

Buildea desde `python:3.12-slim` + SDKs de Huawei. **No** depende del SWR
privado de Huawei: el paquete base `mcp_server_hwc_ops` (extraído de la imagen
original) vive en este repo como source.

```
hwc-ops-bss/
├── Dockerfile
├── requirements.txt
├── entrypoint.py            # instala per_request_creds + registra tools BSS + arranca
└── mcp_server_hwc_ops/
    ├── server.py            # base: ~38 tools ops read-only
    ├── run.py               # transports: stdio / sse / http
    ├── bss_tools.py         # extensión: 3 tools BSS (billing/cost)
    ├── per_request_creds.py # extensión: creds por request (multi-tenant)
    └── config/config.yaml
```

### Tools BSS (nuestra extensión)

- `bss_list_resource_records(cycle, cloud_service_type?, limit?)` — fee records crudos de un ciclo.
- `bss_total_cost(cycle)` — total facturado + breakdown por servicio.
- `bss_cycle_breakdown(cycle)` — breakdown por servicio y por recurso (incluye recursos dados de baja).

BSS usa `GlobalCredentials` y región global `ap-southeast-1`. Pagina hasta 5000
records (~90s en frío); hay cache in-memory + disco para ciclos cerrados
(inmutables). Toda key de cache lleva huella de cuenta → seguro en multi-tenant.

### Credenciales

Dos modos:

- **Single-tenant** (`HWC_REQUIRE_PER_REQUEST_CREDS=0`, default): el contenedor
  usa `HUAWEI_ACCESS_KEY`/`HUAWEI_SECRET_KEY` del entorno para todo request.
- **Multi-tenant** (`HWC_REQUIRE_PER_REQUEST_CREDS=1`): el contenedor no guarda
  secretos. La app cliente manda las creds del usuario en headers HTTP en cada
  call y `per_request_creds` las levanta. Si un request llega sin creds, **falla**
  (no cae a la cuenta del operador).

## terraform-mcp

Imagen Go del SWR de Huawei. No se buildea acá — ver [`terraform-mcp/README.md`](terraform-mcp/README.md)
para alternativas si no tenés acceso al SWR.

## Integración con agent-huawei-cloud

Si corrés este compose junto al `agent-huawei-cloud` (misma red de compose),
apuntá en el `.env` del agente:

```
MCP_HUAWEI_URL=http://hwc-ops-mcp:8080
MCP_TERRAFORM_URL=http://terraform-mcp:8080
```

Si corrés los MCPs sueltos en el host:

```
MCP_HUAWEI_URL=http://localhost:8888
MCP_TERRAFORM_URL=http://localhost:8088
```

## Notas

- El `hwc-ops-bss` sólo expone tools de **lectura** del lado del agente
  (`*_list_*`, `*_show_*`, `iam_get_*`, `bss_*`). Las de escritura
  (`ecs_create_server`, `vpc_delete_vpc`, etc.) existen en `server.py` pero el
  agente las bloquea por allowlist y rutea la mutación por Terraform plan/apply.
- Versiones pinneadas en `requirements.txt` (extraídas del contenedor en producción).
