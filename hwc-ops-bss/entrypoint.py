"""Entrypoint de la imagen hwc-ops extendida con BSS.

Orden importante:
  1. `per_request_creds.install()` — parchea `server._get_credentials` ANTES de
     que los módulos de tools lo importen por nombre.
  2. `bss_tools` — side-effect: registra los tools BSS sobre la instancia `mcp`.
  3. `run.main()` — arranca el server original sin tocar su transporte/args.
"""
from mcp_server_hwc_ops import per_request_creds

per_request_creds.install()

import mcp_server_hwc_ops.bss_tools  # noqa: E402,F401 — registra tools BSS
from mcp_server_hwc_ops.run import main  # noqa: E402

if __name__ == "__main__":
    main()
