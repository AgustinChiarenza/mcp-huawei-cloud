"""Credenciales por request para el MCP hwc-ops.

**El problema.** La imagen base arranca con UNA AK/SK en el entorno
(`HUAWEI_ACCESS_KEY`/`HUAWEI_SECRET_KEY`) y sus ~38 tools responden siempre
sobre esa cuenta. En un deploy multi-usuario eso significa que cualquiera que
pregunte "qué ECS tengo" o "cuánto gasté" recibe la infra y los costos del
operador. La app lo contuvo ruteando al MCP sólo cuando la cuenta del request
coincide con la del contenedor; esto es el arreglo de fondo.

**La solución.** La app manda las credenciales del usuario en headers HTTP del
request MCP y acá reemplazamos `server._get_credentials` para que las prefiera.
El contenedor deja de tener una cuenta propia: pasa a ser stateless respecto de
las credenciales.

**Por qué un monkeypatch y no un fork.** `mcp-server-hwc-ops` es una imagen de
terceros que vive en el SWR; este directorio ya la extiende (ver Dockerfile).
Parchear el único punto por donde los 38 tools obtienen credenciales es mucho
menos frágil que reescribirlos.

**Fallo ruidoso, no silencioso.** Si no se pueden leer los headers (versión de
FastMCP sin `get_http_headers`, request sin contexto HTTP), el default es caer a
las credenciales del entorno — que es el comportamiento de siempre. Con
`HWC_REQUIRE_PER_REQUEST_CREDS=1` ese fallback se convierte en error: preferimos
que el tool falle a que devuelva datos de otra cuenta sin avisar. Si activás las
credenciales por request, activá también ese flag.
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys

logger = logging.getLogger(__name__)

AK_HEADER = "x-huawei-access-key"
SK_HEADER = "x-huawei-secret-key"
REGION_HEADER = "x-huawei-region"

REQUIRE_PER_REQUEST = os.environ.get("HWC_REQUIRE_PER_REQUEST_CREDS", "0") == "1"


class MissingRequestCredentials(RuntimeError):
    """No llegaron credenciales en el request y el fallback está prohibido."""


def _http_headers() -> dict[str, str]:
    """Headers del request MCP en curso, en minúscula. {} si no hay contexto."""
    try:
        from fastmcp.server.dependencies import get_http_headers
    except Exception:  # FastMCP viejo o transporte no-HTTP
        return {}
    try:
        return {str(k).lower(): v for k, v in (get_http_headers() or {}).items()}
    except Exception:  # noqa: BLE001 — fuera de un request HTTP
        return {}


def request_credentials() -> tuple[str, str] | None:
    """(ak, sk) del request en curso, o None si no vinieron."""
    headers = _http_headers()
    ak = (headers.get(AK_HEADER) or "").strip()
    sk = (headers.get(SK_HEADER) or "").strip()
    return (ak, sk) if ak and sk else None


def request_region() -> str | None:
    return (_http_headers().get(REGION_HEADER) or "").strip() or None


def account_fingerprint() -> str:
    """Huella estable y no reversible de la cuenta del request.

    Los caches del MCP DEBEN incluirla: sirviendo varias cuentas, una key sin
    dimensión de cuenta le entrega la factura de un tenant al siguiente.
    """
    creds = request_credentials()
    ak = creds[0] if creds else os.environ.get("HUAWEI_ACCESS_KEY", "")
    if not ak:
        return "noaccount"
    return hashlib.sha256(ak.encode("utf-8")).hexdigest()[:16]


def install() -> None:
    """Reemplaza `server._get_credentials` por la versión per-request.

    Hay que llamarla ANTES de importar los módulos de tools: los que hacen
    `from .server import _get_credentials` se quedan con la referencia que había
    al momento de su import. Por las dudas, también se recorre `sys.modules`
    reemplazando las referencias viejas que hayan quedado.
    """
    from mcp_server_hwc_ops import server

    original = server._get_credentials
    if getattr(original, "_per_request_patched", False):
        return

    def _get_credentials():  # noqa: ANN202 — misma firma que el original: -> (ak, sk)
        creds = request_credentials()
        if creds is not None:
            return creds
        if REQUIRE_PER_REQUEST:
            raise MissingRequestCredentials(
                "El request no trae credenciales Huawei (headers X-Huawei-Access-Key / "
                "X-Huawei-Secret-Key) y HWC_REQUIRE_PER_REQUEST_CREDS=1 prohíbe usar las "
                "del entorno. Se corta acá para no responder con la cuenta equivocada."
            )
        return original()

    _get_credentials._per_request_patched = True
    server._get_credentials = _get_credentials

    rebound = 0
    for name, module in list(sys.modules.items()):
        if not name.startswith("mcp_server_hwc_ops"):
            continue
        if getattr(module, "_get_credentials", None) is original:
            module._get_credentials = _get_credentials
            rebound += 1

    logger.info(
        "hwc-ops: credenciales por request activas (require=%s, refs re-bindeadas=%d)",
        REQUIRE_PER_REQUEST, rebound,
    )
