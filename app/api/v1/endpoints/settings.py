from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import SessionDep, get_current_active_admin
from app.database.repositories.config_repo import get_config_repo
from app.database.models import Kullanici

router = APIRouter()

# Allowed configuration keys whitelist
ALLOWED_CONFIG_KEYS = {
    "filo_hedef_tuketim", "anormal_ust_sinir", "anormal_alt_sinir",
    "uzun_periyot_esigi", "otomatik_yedekleme", "yedek_gunu",
    "default_fuel_price", "notification_enabled", "theme",
    "language", "timezone", "max_report_days"
}

@router.get("/")
async def get_settings(
    db: SessionDep,
    current_admin: Kullanici = Depends(get_current_active_admin)
):
    """Tüm sistem ayarlarını getir (Sadece Admin)"""
    config_repo = get_config_repo(db)
    return await config_repo.get_all_settings()

@router.post("/")
async def update_setting(
    key: str,
    value: str,
    description: str = "",
    db: SessionDep = None,  # None default, FastAPI ile DI çalışır
    current_admin: Kullanici = Depends(get_current_active_admin)
):
    """Sistem ayarını güncelle veya ekle (Sadece Admin)"""
    # Key whitelist validation
    if key not in ALLOWED_CONFIG_KEYS:
        raise HTTPException(
            status_code=400, 
            detail=f"Geçersiz ayar anahtarı: {key}. İzin verilenler: {', '.join(sorted(ALLOWED_CONFIG_KEYS))}"
        )
    config_repo = get_config_repo(db)
    await config_repo.set_value(key, value, description)
    return {"status": "success", "message": f"Ayar '{key}' başarıyla güncellendi."}

@router.get("/{key}")
async def get_setting_by_key(
    key: str,
    db: SessionDep,
    current_admin: Kullanici = Depends(get_current_active_admin)
):
    """Belirli bir ayarın değerini getir"""
    config_repo = get_config_repo(db)
    val = await config_repo.get_value(key)
    if val is None:
        raise HTTPException(status_code=404, detail="Ayar bulunamadı.")
    return {key: val}
