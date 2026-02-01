from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.services.health_service import HealthService, get_health_service

router = APIRouter()

@router.get("/")
async def health_check(
    service: HealthService = Depends(get_health_service)
) -> Dict[str, Any]:
    """
    Sistem Sağlık Durumu (Liveness/Readiness Probe)
    """
    return await service.get_full_status()
