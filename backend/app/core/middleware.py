from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.platform_metrics import api_metrics

logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        started_at = perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            api_metrics.observe(duration_ms, response.status_code)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            return response
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
