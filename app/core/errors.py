from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any, Dict
import uuid
import time

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class BusinessException(Exception):
    """İş mantığı hataları için base class"""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR", details: Any = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

def create_error_response(
    status_code: int,
    message: str,
    code: str,
    request_id: str,
    details: Any = None
) -> JSONResponse:
    """Standart Hata Yanıtı Oluşturucu"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
                "timestamp": time.time()
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Beklenmeyen tüm hataları yakalar (500).
    Stack trace loglar ancak kullanıcıya güvenli mesaj döner.
    """
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Detaylı loglama (Kritik)
    logger.error(
        f"Unhandled Exception: {str(exc)}", 
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Sunucu tarafında beklenmeyen bir hata oluştu. Lütfen destek ekibiyle iletişime geçin.",
        code="INTERNAL_SERVER_ERROR",
        request_id=request_id
    )

async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """Özel iş mantığı hatalarını yakalar"""
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    logger.warning(f"Business Error: {exc.message}", extra={"code": exc.code})
    
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message=exc.message,
        code=exc.code,
        request_id=request_id,
        details=exc.details
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic validasyon hatalarını formatlar"""
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Hata detaylarını basitleştir
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"]) if error["loc"] else "body"
        errors.append({"field": field, "message": error["msg"]})
        
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Veri doğrulama hatası.",
        code="VALIDATION_ERROR",
        request_id=request_id,
        details=errors
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """FastAPI/Starlette HTTP hatalarını yakalar (404, 401 vb.)"""
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        code=f"HTTP_{exc.status_code}",
        request_id=request_id
    )
