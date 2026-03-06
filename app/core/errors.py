import time
import uuid
from typing import Any, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class DiagnosticHelper:
    """
    Kullanıcı hataları için otomatik teşhis ve çözüm önerisi sunar (Phase 4).
    """

    SUGGESTED_FIXES = {
        "BUSINESS_ERROR": "İş kuralı ihlali tespit edildi. Girdiğiniz verilerin limitler dahilinde olduğundan emin olun.",
        "VALIDATION_ERROR": "Form verileri geçersiz. Lütfen kırmızı ile işaretlenen alanları kontrol edin.",
        "DB_ERROR": "Veritabanı bağlantı hatası. Lütfen bir süre sonra tekrar deneyin veya sistem yöneticisine bildirin.",
        "AUTH_ERROR": "Oturumunuzun süresi dolmuş olabilir. Lütfen tekrar giriş yapın.",
        "EMPTY_TRIP_WITH_LOAD": "Boş sefer (bos_sefer) olarak işaretlenen bir kayıtta yük (tonaj) girişi yapılamaz. Lütfen yükü 0 yapın veya bayrağı kaldırın.",
        "ANALYSIS_GAP": "Analiz için yeterli veri periyodu bulunamadı. Lütfen daha fazla yakıt veya sefer verisi ekleyin.",
    }

    @classmethod
    def get_suggestion(cls, code: str, message: str) -> Optional[str]:
        # Özel mesaj pattern eşleşmesi
        if "bos_sefer" in message.lower() and "ton" in message.lower():
            return cls.SUGGESTED_FIXES["EMPTY_TRIP_WITH_LOAD"]

        if "gap" in message.lower() or "periyot" in message.lower():
            return cls.SUGGESTED_FIXES["ANALYSIS_GAP"]

        return cls.SUGGESTED_FIXES.get(code)


class BusinessException(Exception):
    """İş mantığı hataları için base class"""

    def __init__(self, message: str, code: str = "BUSINESS_ERROR", details: Any = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


def create_error_response(
    status_code: int, message: str, code: str, request_id: str, details: Any = None
) -> JSONResponse:
    """Standart Hata Yanıtı Oluşturucu"""
    suggestion = DiagnosticHelper.get_suggestion(code, message)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "suggestion": suggestion,  # Phase 4
                "request_id": request_id,
                "timestamp": time.time(),
            },
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Beklenmeyen tüm hataları yakalar (500).
    Stack trace loglar ancak kullanıcıya güvenli mesaj döner.
    """
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    # Detaylı loglama (Kritik)
    logger.error(
        f"Unhandled Exception: {exc!s}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Sunucu tarafında beklenmeyen bir hata oluştu. Lütfen destek ekibiyle iletişime geçin.",
        code="INTERNAL_SERVER_ERROR",
        request_id=request_id,
    )


async def business_exception_handler(
    request: Request, exc: BusinessException
) -> JSONResponse:
    """Özel iş mantığı hatalarını yakalar"""
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    logger.warning(f"Business Error: {exc.message}", extra={"code": exc.code})

    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message=exc.message,
        code=exc.code,
        request_id=request_id,
        details=exc.details,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
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
        details=errors,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """FastAPI/Starlette HTTP hatalarını yakalar (404, 401 vb.)"""
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        code=f"HTTP_{exc.status_code}",
        request_id=request_id,
    )
