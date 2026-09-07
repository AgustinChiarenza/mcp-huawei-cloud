# hwc-ops-bss — MCP de Huawei Cloud Ops (ECS/VPC/OBS/...) + BSS (billing/cost)
#
# Autocontenido: buildea desde python:3.12-slim con las SDKs de Huawei y el
# paquete mcp_server_hwc_ops (base + tools BSS + credenciales por request).
# No depende del SWR privado de Huawei.
#
# Build:  docker build -t hwc-ops-bss:dev ./hwc-ops-bss
# Run:    docker run --rm -p 8888:8080 -e HUAWEI_ACCESS_KEY=... -e HUAWEI_SECRET_KEY=... hwc-ops-bss:dev -t http -p 8080
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Paquete base + extensión (bss_tools, per_request_creds) viven en site-packages
COPY mcp_server_hwc_ops /usr/local/lib/python3.12/site-packages/mcp_server_hwc_ops
COPY entrypoint.py /app/entrypoint.py

# Cache de disco BSS para ciclos cerrados (inmutables). Sobrevive restarts.
RUN mkdir -p /tmp/bss_cache
ENV BSS_CACHE_DIR=/tmp/bss_cache

EXPOSE 8080

# El entrypoint instala per_request_creds, registra tools BSS y arranca el server.
# Args (-t http -p 8080) los pasás vía command en compose.
ENTRYPOINT ["python3", "/app/entrypoint.py"]
CMD ["-t", "http", "-p", "8080"]
