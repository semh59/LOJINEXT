from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.infrastructure.security.permission_checker import require_yetki
from app.database.models import Kullanici
from app.schemas.user import KullaniciRead, KullaniciCreate, KullaniciUpdate
from app.core.services.user_service import UserService
from app.infrastructure.logging.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=List[KullaniciRead])
async def list_users(
    current_user: Kullanici = Depends(require_yetki("kullanici_goruntule")),
    skip: int = 0,
    limit: int = 100,
):
    """Kullanıcıları listele"""
    service = UserService()
    return await service.list_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=KullaniciRead)
async def get_user(
    user_id: int,
    current_user: Kullanici = Depends(require_yetki("kullanici_goruntule")),
):
    """Kullanıcı detayını getir"""
    service = UserService()
    return await service.get_user(user_id)


@router.post("/", response_model=KullaniciRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: KullaniciCreate,
    current_user: Kullanici = Depends(require_yetki("kullanici_ekle")),
):
    """Yeni kullanıcı oluştur"""
    service = UserService()
    return await service.create_user(data.model_dump(), created_by_id=current_user.id)


@router.put("/{user_id}", response_model=KullaniciRead)
async def update_user(
    user_id: int,
    data: KullaniciUpdate,
    current_user: Kullanici = Depends(require_yetki("kullanici_duzenle")),
):
    """Kullanıcıyı güncelle"""
    service = UserService()
    # Filter out None values to avoid overwriting with nulls if update schema allows partials
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await service.update_user(user_id, update_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: Kullanici = Depends(require_yetki("kullanici_sil")),
):
    """Kullanıcıyı sil"""
    service = UserService()
    success = await service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return None
