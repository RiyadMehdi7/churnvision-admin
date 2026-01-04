import time
from typing import Dict, Callable
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RateLimitData:
    """Stores rate limit data for a single client"""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests: list[float] = []

    def is_rate_limited(self) -> bool:
        """Check if the client has exceeded rate limit"""
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [t for t in self.requests if now - t < 60]
        return len(self.requests) >= self.requests_per_minute

    def add_request(self) -> None:
        """Record a new request"""
        self.requests.append(time.time())

    def get_retry_after(self) -> int:
        """Get seconds until rate limit resets"""
        if not self.requests:
            return 0
        oldest = min(self.requests)
        return max(0, int(60 - (time.time() - oldest)))


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter middleware.
    For production, consider using Redis-based rate limiting.
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        exclude_paths: list[str] = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
        self.clients: Dict[str, RateLimitData] = defaultdict(
            lambda: RateLimitData(self.requests_per_minute)
        )

    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for the client"""
        # Use API key if present, otherwise use IP
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:8]}"

        # Get client IP (handle proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        return f"ip:{request.client.host if request.client else 'unknown'}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        client_id = self._get_client_id(request)
        client_data = self.clients[client_id]

        if client_data.is_rate_limited():
            retry_after = client_data.get_retry_after()
            logger.warning(
                f"Rate limit exceeded for {client_id}",
                extra={"client_id": client_id, "retry_after": retry_after}
            )
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        client_data.add_request()
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = max(0, self.requests_per_minute - len(client_data.requests))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
