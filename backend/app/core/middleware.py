from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("http.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        client_host = request.client.host if request.client else "unknown"
        logger.info(
            "--> %s %s [client=%s req_id=%s]",
            request.method,
            request.url.path,
            client_host,
            request_id,
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            level = logger.info if response.status_code < 400 else logger.warning
            level(
                "<-- %s %s %d [%.2fms req_id=%s]",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request_id,
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "<-- %s %s ERROR: %s [%.2fms req_id=%s]",
                request.method,
                request.url.path,
                str(exc),
                duration_ms,
                request_id,
            )
            raise exc
