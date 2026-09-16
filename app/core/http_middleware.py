import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.request_context import reset_request_id, set_request_id


logger = logging.getLogger("app.http")
REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)


def valid_request_id(value: str | None) -> bool:
    return value is not None and len(value) == 36 and _REQUEST_ID_PATTERN.fullmatch(value) is not None


class HttpObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming.lower() if valid_request_id(incoming) else str(uuid4())
        token = set_request_id(request_id)
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            logger.exception(
                "Unhandled request exception",
                extra={
                    "event": "http.request.exception",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
            return response
        finally:
            duration_ms = round((perf_counter() - started) * 1000, 3)
            logger.info(
                "Request completed",
                extra={
                    "event": "http.request.completed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            # A response may not exist after an exception; successful and HTTP-error
            # responses always pass through this branch before context cleanup.
            if "response" in locals():
                response.headers[REQUEST_ID_HEADER] = request_id
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["Referrer-Policy"] = "no-referrer"
            reset_request_id(token)
