import time
import uuid
import json
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enterprise-grade Request Logging Middleware.
    
    Özellikler:
    - X-Correlation-ID takibi (Distributed tracing için)
    - İstek süresi ölçümü (Latency)
    - İstek ve yanıt detaylarının loglanması (JSON)
    - Hassas verilerin maskelenmesi (Body logging kapalı tutulur)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    def _mask_path(self, path: str) -> str:
        """Query parametrelerindeki hassas verileri maskele"""
        import re
        # token=..., password=..., key=..., secret=...
        pattern = r'(token|password|key|secret|api_key)=([^&]+)'
        return re.sub(pattern, r'\1=***', path)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 1. Correlation ID Yönetimi
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # 2. İstek Logu (Structured)
        client_host = request.client.host if request.client else "unknown"
        
        masked_path = self._mask_path(str(request.url))
        # Sadece path kısmını al (query param dahil tüm URL'i maskeledik)
        
        request_log = {
            "event": "request_received",
            "correlation_id": correlation_id,
            "method": request.method,
            "path": masked_path,
            "client_ip": client_host,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        logger.info(f"Incoming Request: {request.method} {masked_path}", extra=request_log)

        try:
            # 3. İsteğin İşlenmesi
            response = await call_next(request)
            
            # Response Header'a ID ekle
            response.headers["X-Correlation-ID"] = correlation_id
            
            # 4. Yanıt Logu (Success)
            process_time = (time.time() - start_time) * 1000  # ms
            
            # Security headers ekle
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            response_log = {
                "event": "request_processed",
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "latency_ms": round(process_time, 2),
                "path": masked_path
            }
            
            # Performans uyarısı (>1s yavaş kabul edilir)
            if process_time > 1000:
                logger.warning(
                    f"Slow Request: {request.method} {request.url.path} took {process_time:.2f}ms", 
                    extra=response_log
                )
            else:
                logger.info(
                    f"Request Completed: {response.status_code}", 
                    extra=response_log
                )
                
            return response

        except Exception as e:
            # 5. Hata Logu (Exception)
            process_time = (time.time() - start_time) * 1000
            
            error_log = {
                "event": "request_failed",
                "correlation_id": correlation_id,
                "error": str(e),
                "latency_ms": round(process_time, 2),
                "path": request.url.path
            }
            logger.error(
                f"Request Failed: {str(e)}", 
                extra=error_log, 
                exc_info=True
            )
            raise e
