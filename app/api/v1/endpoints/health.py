from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.services.health_service import HealthService, get_health_service

router = APIRouter()


@router.get("/")
async def health_check(
    service: HealthService = Depends(get_health_service),
) -> Dict[str, Any]:
    """
    Sistem Saglik Durumu (Liveness/Readiness Probe)
    """
    status = await service.get_full_status()

    critical_down = status["components"]["database"]["status"] != "healthy"
    http_status = 503 if critical_down else 200

    return JSONResponse(status_code=http_status, content=status)
