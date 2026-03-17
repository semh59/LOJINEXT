"""
Rate Limiting Middleware
IP bazlÃ„Â± istek sÃ„Â±nÃ„Â±rlama (DoS korumasÃ„Â±)
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    Production ortamÃ„Â± iÃƒÂ§in Redis-backed ÃƒÂ§ÃƒÂ¶zÃƒÂ¼m ÃƒÂ¶nerilir.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 dakika
        # IP -> (request_count, window_start_time)
        self.request_counts: Dict[str, Tuple[int, float]] = defaultdict(
            lambda: (0, time.time())
        )

    async def dispatch(self, request: Request, call_next):
        # Rate limiting'i atlayacak endpoint'ler
        skip_paths = [
            "/docs",
            "/openapi.json",
            "/",
            "/api/v1/auth/token",
            "/api/v1/ai/status",
            "/api/v1/ai/chat",
            "/api/v1/ai/progress",
        ]
        import sys
        from app.config import settings

        if (
            request.url.path in skip_paths
            or settings.ENVIRONMENT == "dev"
            or "pytest" in sys.modules
        ):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-ID")
        bucket = f"{client_ip}:{user_id or 'anon'}:{request.url.path}"
        current_time = time.time()

        count, window_start = self.request_counts[bucket]

        # Window sÃƒÂ¼resi dolmuÃ…Å¸sa sÃ„Â±fÃ„Â±rla
        if current_time - window_start >= self.window_size:
            self.request_counts[bucket] = (1, current_time)
        else:
            # Limit aÃ…Å¸Ã„Â±ldÃ„Â± mÃ„Â± kontrol et
            if count >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for bucket: {bucket}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": int(
                            self.window_size - (current_time - window_start)
                        ),
                    },
                    headers={
                        "Retry-After": str(
                            int(self.window_size - (current_time - window_start))
                        )
                    },
                )
            # SayacÃ„Â± artÃ„Â±r
            self.request_counts[bucket] = (count + 1, window_start)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """GerÃƒÂ§ek client IP'sini al (proxy arkasÃ„Â± dahil)."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
