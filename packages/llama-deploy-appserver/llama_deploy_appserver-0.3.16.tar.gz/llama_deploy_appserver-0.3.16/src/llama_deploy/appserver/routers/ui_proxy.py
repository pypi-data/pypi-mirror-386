import asyncio
import logging
from contextlib import suppress
from typing import List

import httpx
import websockets
from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
)
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from llama_deploy.appserver.configure_logging import suppress_httpx_logs
from llama_deploy.appserver.interrupts import (
    OperationAborted,
    shutdown_event,
    wait_or_abort,
)
from llama_deploy.appserver.settings import ApiserverSettings
from llama_deploy.core.client.ssl_util import get_httpx_verify_param
from llama_deploy.core.deployment_config import DeploymentConfig

logger = logging.getLogger(__name__)


async def _ws_proxy(ws: WebSocket, upstream_url: str) -> None:
    """Proxy WebSocket connection to upstream server."""
    if shutdown_event.is_set():
        await ws.close()
        return

    # Defer accept until after upstream connects so we can mirror the selected subprotocol

    # Forward most headers except WebSocket-specific ones
    header_prefix_blacklist = ["sec-websocket-"]
    header_blacklist = {
        "host",
        "connection",
        "upgrade",
    }
    hdrs = []
    for k, v in ws.headers.items():
        if k.lower() not in header_blacklist:
            for prefix in header_prefix_blacklist:
                if k.lower().startswith(prefix):
                    break
            else:
                hdrs.append((k, v))

    try:
        # Parse subprotocols if present
        subprotocols: List[str] | None = None
        requested = ws.headers.get("sec-websocket-protocol")
        if requested:
            # Parse comma-separated subprotocols (as plain strings)
            subprotocols = [p.strip() for p in requested.split(",")]

        # Open upstream WebSocket connection, offering the same subprotocols
        async with websockets.connect(
            upstream_url,
            additional_headers=hdrs,
            subprotocols=subprotocols,
            open_timeout=5,
        ) as upstream:
            await ws.accept(subprotocol=upstream.subprotocol)

            async def client_to_upstream() -> None:
                try:
                    while True:
                        msg = await wait_or_abort(ws.receive(), shutdown_event)
                        if msg["type"] == "websocket.receive":
                            if "text" in msg:
                                await upstream.send(msg["text"])
                            elif "bytes" in msg:
                                await upstream.send(msg["bytes"])
                        elif msg["type"] == "websocket.disconnect":
                            break
                except OperationAborted:
                    pass
                except Exception:
                    pass

            async def upstream_to_client() -> None:
                try:
                    while True:
                        message = await wait_or_abort(upstream.recv(), shutdown_event)
                        if isinstance(message, str):
                            await ws.send_text(message)
                        else:
                            await ws.send_bytes(message)
                except OperationAborted:
                    pass
                except Exception:
                    pass

            # Pump both directions concurrently, cancel the peer when one side closes
            t1 = asyncio.create_task(client_to_upstream())
            t2 = asyncio.create_task(upstream_to_client())
            _, pending = await asyncio.wait(
                {t1, t2}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            # On shutdown, proactively close both sides to break any remaining waits
            if shutdown_event.is_set():
                with suppress(Exception):
                    await ws.close()
                with suppress(Exception):
                    await upstream.close()

    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
        # Accept then close so clients (and TestClient) don't error on enter
        with suppress(Exception):
            await ws.accept()
        with suppress(Exception):
            await ws.close()
    finally:
        try:
            await ws.close()
        except Exception as e:
            logger.debug(f"Error closing client connection: {e}")


def create_ui_proxy_router(name: str, port: int) -> APIRouter:
    deployment_router = APIRouter(
        prefix=f"/deployments/{name}",
        tags=["deployments"],
    )

    @deployment_router.websocket("/ui/{path:path}")
    @deployment_router.websocket("/ui")
    async def websocket_proxy(
        websocket: WebSocket,
        path: str | None = None,
    ) -> None:
        # Build the upstream WebSocket URL using FastAPI's extracted path parameter
        slash_path = f"/{path}" if path is not None else ""
        upstream_path = f"/deployments/{name}/ui{slash_path}"

        # Convert to WebSocket URL
        upstream_url = f"ws://localhost:{port}{upstream_path}"
        if websocket.url.query:
            upstream_url += f"?{websocket.url.query}"

        await _ws_proxy(websocket, upstream_url)

    @deployment_router.api_route(
        "/ui/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        include_in_schema=False,
    )
    @deployment_router.api_route(
        "/ui",
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        include_in_schema=False,
    )
    async def proxy(
        request: Request,
        path: str | None = None,
    ) -> StreamingResponse:
        # Build the upstream URL using FastAPI's extracted path parameter
        slash_path = f"/{path}" if path else ""
        upstream_path = f"/deployments/{name}/ui{slash_path}"

        upstream_url = httpx.URL(f"http://localhost:{port}{upstream_path}").copy_with(
            params=request.query_params
        )

        # Debug logging
        logger.debug(f"Proxying {request.method} {request.url} -> {upstream_url}")

        # Strip hop-by-hop headers + host
        hop_by_hop = {
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",  # codespell:ignore
            "trailers",
            "transfer-encoding",
            "upgrade",
            "host",
        }
        headers = {
            k: v for k, v in request.headers.items() if k.lower() not in hop_by_hop
        }

        try:
            client = httpx.AsyncClient(timeout=None, verify=get_httpx_verify_param())

            req = client.build_request(
                request.method,
                upstream_url,
                headers=headers,
                content=request.stream(),  # stream uploads
            )
            async with suppress_httpx_logs():
                upstream = await client.send(req, stream=True)

            resp_headers = {
                k: v for k, v in upstream.headers.items() if k.lower() not in hop_by_hop
            }

            # Stream downloads and ensure cleanup in the generator's finally block
            async def upstream_body():
                try:
                    async for chunk in upstream.aiter_raw():
                        yield chunk
                finally:
                    try:
                        await upstream.aclose()
                    finally:
                        await client.aclose()

            return StreamingResponse(
                upstream_body(),
                status_code=upstream.status_code,
                headers=resp_headers,
            )

        except httpx.ConnectError:
            raise HTTPException(status_code=502, detail="Upstream server unavailable")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Upstream server timeout")
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            raise HTTPException(status_code=502, detail="Proxy error")

    return deployment_router


def mount_static_files(
    app: FastAPI, config: DeploymentConfig, settings: ApiserverSettings
) -> None:
    path = settings.app_root / config.build_output_path()
    if not path:
        return

    if not path.exists():
        return

    # Serve index.html when accessing the directory path
    app.mount(
        f"/deployments/{config.name}/ui",
        StaticFiles(directory=str(path), html=True),
        name=f"ui-static-{config.name}",
    )
    return None
