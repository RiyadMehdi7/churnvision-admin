import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler middleware"""

    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except ValidationError as e:
            logger.error(
                "Validation error",
                extra={"errors": e.errors(), "path": request.url.path},
            )
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Validation error",
                    "errors": e.errors() if self.debug else None,
                },
            )

        except SQLAlchemyError as e:
            logger.error(
                "Database error",
                extra={"error": str(e), "path": request.url.path},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Database error occurred",
                    "error": str(e) if self.debug else None,
                },
            )

        except PermissionError as e:
            logger.warning(
                "Permission denied",
                extra={"error": str(e), "path": request.url.path},
            )
            return JSONResponse(
                status_code=403,
                content={"detail": str(e) or "Permission denied"},
            )

        except FileNotFoundError as e:
            logger.warning(
                "Resource not found",
                extra={"error": str(e), "path": request.url.path},
            )
            return JSONResponse(
                status_code=404,
                content={"detail": str(e) or "Resource not found"},
            )

        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"Unhandled exception: {str(e)}",
                extra={
                    "error": str(e),
                    "traceback": traceback.format_exc() if self.debug else None,
                    "request_id": request_id,
                    "path": request.url.path,
                },
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                    "error": str(e) if self.debug else None,
                },
            )
