"""
Rate Limiting Middleware
IP bazlı istek sınırlama (DoS koruması)
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
    Production ortamı için Redis-backed çözüm önerilir.
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
        current_time = time.time()

        count, window_start = self.request_counts[client_ip]

        # Window süresi dolmuşsa sıfırla
        if current_time - window_start >= self.window_size:
            self.request_counts[client_ip] = (1, current_time)
        else:
            # Limit aşıldı mı kontrol et
            if count >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
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
            # Sayacı artır
            self.request_counts[client_ip] = (count + 1, window_start)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Gerçek client IP'sini al (proxy arkası dahil)."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
