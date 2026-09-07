import argparse
import asyncio
import contextlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import AsyncIterator

import uvicorn
import yaml
from mcp.server.fastmcp.utilities.logging import configure_logging, get_logger
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from .server import mcp

logger = get_logger(__name__)
configure_logging("INFO")


def _load_config_defaults():
    """Load default transport/port from config.yaml if present."""
    config_path = Path(__file__).parent / "config" / "config.yaml"
    defaults = {"transport": "stdio", "port": 8888}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        if cfg.get("transport"):
            defaults["transport"] = cfg["transport"]
        if cfg.get("port"):
            defaults["port"] = int(cfg["port"])
    except FileNotFoundError:
        pass
    return defaults


async def _run_stdio():
    """Run the MCP server using stdio transport."""
    logger.info("Starting hwc-mcp-server-ops with transport=stdio")
    async with stdio_server() as streams:
        await mcp._mcp_server.run(
            streams[0], streams[1], mcp._mcp_server.create_initialization_options()
        )


async def _run_sse(port: int):
    """Run the MCP server using SSE transport."""
    logger.info(f"Starting hwc-mcp-server-ops with transport=sse, port={port}")
    sse = SseServerTransport("/messages/")

    async def handle_sse_connection(request):
        client_id = str(uuid.uuid4())
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await mcp._mcp_server.run(
                    streams[0], streams[1], mcp._mcp_server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"SSE error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({"status": "ok"}, status_code=200)

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse_connection),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        debug=True,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_headers=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    await server.serve()


async def _run_http(port: int):
    """Run the MCP server using StreamableHTTP transport."""
    logger.info(f"Starting hwc-mcp-server-ops with transport=http, port={port}")
    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        event_store=None,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    starlette_app = Starlette(
        debug=True,
        routes=[Mount("/mcp", app=handle_streamable_http)],
        lifespan=lifespan,
    )
    http_config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port)
    http_server = uvicorn.Server(http_config)
    await http_server.serve()


def main():
    defaults = _load_config_defaults()

    parser = argparse.ArgumentParser(description="Huawei Cloud Ops MCP Server")
    parser.add_argument(
        "-t",
        "--transport",
        type=str,
        choices=["http", "sse", "stdio"],
        default=None,
        help="Transport mode (stdio, http, sse)",
    )
    parser.add_argument("-p", "--port", type=int, default=None, help="Port for http/sse mode")
    args = parser.parse_args()

    transport = args.transport or os.environ.get("MCP_SERVER_MODE") or defaults["transport"]
    port = args.port or int(os.environ.get("MCP_SERVER_PORT", "0")) or defaults["port"]

    if transport == "stdio":
        asyncio.run(_run_stdio())
    elif transport == "sse":
        asyncio.run(_run_sse(port))
    elif transport == "http":
        asyncio.run(_run_http(port))
    else:
        asyncio.run(_run_stdio())


if __name__ == "__main__":
    main()
