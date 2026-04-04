import time
import uuid
from typing import Iterable

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask

from app.config.config_loader import get_config_value
from app.config.logging import get_logger

logger = get_logger(__name__)

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    filtered: dict[str, str] = {}
    for key, value in headers:
        lower_key = key.lower()
        if lower_key in HOP_BY_HOP_HEADERS:
            continue
        if lower_key == "host":
            continue
        if lower_key == "content-length":
            continue
        filtered[key] = value
    return filtered


def _get_request_id(request: Request) -> str:
    req_id = request.headers.get("X-Request-ID")
    if req_id:
        return req_id
    return str(uuid.uuid4())


def _get_upstream_base(path: str) -> tuple[str, str]:
    if path == "chat":
        return (
            get_config_value(
                "upstreams", "agent", "base_url", default="http://127.0.0.1:8001"
            ),
            "agent",
        )
    return (
        get_config_value(
            "upstreams", "business", "base_url", default="http://127.0.0.1:8000"
        ),
        "business",
    )


def _build_upstream_url(base_url: str, path: str, query: str) -> str:
    base = base_url.rstrip("/")
    if path:
        upstream_path = f"/api/v1/{path}"
    else:
        upstream_path = "/api/v1"
    url = f"{base}{upstream_path}"
    if query:
        url = f"{url}?{query}"
    return url


app = FastAPI(
    title="Lak Chemicals and Hardware API Gateway",
    description="API Gateway for Lak Chemicals and Hardware",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = _get_request_id(request)
    request.state.request_id = request_id

    response: Response | None = None
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = int((time.time() - start_time) * 1000)
        upstream = getattr(request.state, "upstream", "gateway")
        auth_present = "yes" if request.headers.get("Authorization") else "no"
        status_code = response.status_code if response else 500
        logger.info(
            "request completed",
            extra={
                "user": f"auth:{auth_present}",
                "action": "proxy_request",
                "location": request.url.path,
                "request_id": request_id,
                "method": request.method,
                "status": status_code,
                "duration_ms": duration_ms,
                "upstream": upstream,
            },
        )


@app.get("/health")
async def gateway_health():
    return {"message": "API Gateway is healthy"}


@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy_request(path: str, request: Request):
    base_url, upstream_name = _get_upstream_base(path)
    request.state.upstream = upstream_name

    query = request.url.query
    url = _build_upstream_url(base_url, path, query)
    request_id = request.state.request_id

    timeout_default = get_config_value("upstreams", "timeout_seconds", default=10)
    timeout_seconds = 60 if path == "chat" else timeout_default
    timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    headers = _filter_headers(request.headers.items())
    headers["X-Request-ID"] = request_id

    try:
        body = await request.body()
        if path == "chat":
            client = httpx.AsyncClient(timeout=timeout)
            req = client.build_request(
                request.method,
                url,
                headers=headers,
                content=body,
            )
            upstream_response = await client.send(req, stream=True)
            response_headers = _filter_headers(upstream_response.headers.items())
            response_headers["X-Request-ID"] = request_id

            async def close_client():
                await upstream_response.aclose()
                await client.aclose()

            return StreamingResponse(
                upstream_response.aiter_bytes(),
                status_code=upstream_response.status_code,
                headers=response_headers,
                background=BackgroundTask(close_client),
            )

        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_response = await client.request(
                request.method,
                url,
                headers=headers,
                content=body,
            )
            response_headers = _filter_headers(upstream_response.headers.items())
            response_headers["X-Request-ID"] = request_id
            return Response(
                content=upstream_response.content,
                status_code=upstream_response.status_code,
                headers=response_headers,
                media_type=upstream_response.headers.get("content-type"),
            )
    except httpx.TimeoutException:
        logger.warning(
            "upstream timeout",
            extra={
                "user": "system",
                "action": "proxy_timeout",
                "location": request.url.path,
                "upstream": upstream_name,
                "request_id": request_id,
            },
        )
        return JSONResponse(
            status_code=504,
            content={"detail": "Upstream timeout"},
            headers={"X-Request-ID": request_id},
        )
    except Exception as exc:
        logger.error(
            f"upstream error: {exc}",
            extra={
                "user": "system",
                "action": "proxy_error",
                "location": request.url.path,
                "upstream": upstream_name,
                "request_id": request_id,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=502,
            content={"detail": "Bad gateway"},
            headers={"X-Request-ID": request_id},
        )
