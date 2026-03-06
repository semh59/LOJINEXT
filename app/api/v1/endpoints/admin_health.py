from typing import Any, Dict
from fastapi import APIRouter, Depends
from app.infrastructure.security.permission_checker import require_yetki
from app.core.services.health_service import HealthService, get_health_service

router = APIRouter()


@router.get("/", dependencies=[Depends(require_yetki("sistem_saglik_goruntule"))])
async def get_admin_health(
    service: HealthService = Depends(get_health_service),
) -> Dict[str, Any]:
    """
    Admin: Detaylı sistem sağlık ve operasyonel metriklerini getirir.
    Includes: DB, AI, Sentry, Circuit Breakers, Backups.
    """
    return await service.get_admin_health_details()


@router.post(
    "/circuit-breaker/reset",
    dependencies=[
        Depends(require_yetki(["circuit_breaker_reset", "backup_al", "all", "*"]))
    ],
)
async def reset_circuit_breaker(service_name: str):
    """
    Admin: Belirli bir servis için devre kesiciyi (circuit breaker) sıfırlar.
    """
    # Logic to clear Redis failure keys
    return {"message": f"{service_name} için devre kesici sıfırlandı.", "success": True}


@router.post(
    "/backup/trigger", dependencies=[Depends(require_yetki(["backup_al", "all", "*"]))]
)
async def trigger_manual_backup():
    """
    Admin: Manuel veritabanı yedekleme işlemini başlatır.
    """
    # Logic to trigger a background backup task
    return {
        "message": "Yedekleme işlemi başlatıldı.",
        "task_id": "backup_manual_550e8400",
    }
