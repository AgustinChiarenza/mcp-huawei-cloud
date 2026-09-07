# terraform-mcp

MCP server (Go) para lookups contra el Terraform Registry: módulos, providers y
versiones públicas. Se consume vía **streamable HTTP en `/mcp`**.

## Imagen

Este repo **no** incluye el binario ni el source (es un proyecto Go de terceros
que vive en el SWR de Huawei). La imagen usada por el compose es:

```
swr.la-south-2.myhuaweicloud.com/imagenes-varias/terraform-mcp-server:dev
```

Comando de arranque (ya cableado en `docker-compose.yml`):

```
streamable-http --transport-host 0.0.0.0 --transport-port 8080
```

- El `--transport-host 0.0.0.0` es necesario para que otros containers lo
  reachen por service name (el default `127.0.0.1` no se reacha entre containers).
- Loguea un warning "no TFE token" → las tools de registry **privado** quedan
  off, pero el lookup **público** de módulos/providers (lo que usa el agente)
  funciona igual.

## Si no tenés acceso al SWR

Opciones:

1. **Upstream open-source.** El `terraform-mcp-server` es open-source. Clonar el
   repo oficial y `go build` + empaquetar en una imagen minimal (`gcr.io/distroless/static`
   o `scratch` con el binario).
2. **Extraer el binario de la imagen** (si tenés acceso desde otra máquina):
   ```
   docker create --name tmp swr.la-south-2.myhuaweicloud.com/imagenes-varias/terraform-mcp-server:dev
   docker cp tmp:/app/terraform-mcp-server ./terraform-mcp-server   # path a confirmar
   docker rm tmp
   ```
   y armar una imagen `scratch` con ese binario.
3. **Skopeo / crane** para copiar la imagen del SWR a un registry propio sin
   tener que pull localmente.

## Tools expuestas (públicas, sin TFE token)

- `get_latest_provider_version{namespace, name}` — última versión de un provider.
- `search_modules{module_query}` — busca módulos en el registry público.
- (+ tools de registry privado si hay `TFE_TOKEN`).
