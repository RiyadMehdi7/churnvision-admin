import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""

    def __init__(self, app: ASGIApp, exclude_paths: list[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Create request-scoped logger
        request_logger = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        # Log request
        request_logger.info(f"Request started: {request.method} {request.url.path}")

        # Track timing
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            request_logger.info(
                f"Request completed: {response.status_code}",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2),
                },
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))

            return response

        except Exception as e:
            process_time = time.time() - start_time
            request_logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "error": str(e),
                    "duration_ms": round(process_time * 1000, 2),
                },
            )
            raise
