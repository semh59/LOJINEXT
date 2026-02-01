from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from app.api.deps import SessionDep, get_current_active_admin
from app.database.models import Kullanici
from app.schemas.user import KullaniciRead, KullaniciCreate, KullaniciUpdate
from app.core.security import get_password_hash

from app.infrastructure.logging.logger import get_logger
from fastapi import APIRouter, Depends, HTTPException, status, Query

logger = get_logger(__name__)

router = APIRouter()

@router.get("/", response_model=List[KullaniciRead])
async def get_users(
    db: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = 100,
    current_admin: Kullanici = Depends(get_current_active_admin)
):
    """Tüm kullanıcıları listele (Sadece Admin)"""
    from app.config import settings
    limit = min(limit, settings.MAX_PAGINATION_LIMIT)
    
    result = await db.execute(
        select(Kullanici).order_by(Kullanici.id).offset(skip).limit(limit)
    )
    return result.scalars().all()

@router.post("/", response_model=KullaniciRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: SessionDep,
    user_in: KullaniciCreate,
    current_admin: Kullanici = Depends(get_current_active_admin)
):
    """Yeni kullanıcı oluştur (Sadece Admin)"""
    # Kullanıcı adı kontrolü
    result = await db.execute(select(Kullanici).where(Kullanici.kullanici_adi == user_in.kullanici_adi))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanımda.")
    
    db_obj = Kullanici(
        kullanici_adi=user_in.kullanici_adi,
        sifre_hash=get_password_hash(user_in.sifre),
        ad_soyad=user_in.ad_soyad,
        rol=user_in.rol,
        aktif=user_in.aktif
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    logger.info(f"User created: {db_obj.kullanici_adi} by admin {current_admin.kullanici_adi}")
    return db_obj

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: SessionDep,
    current_admin: Kullanici = Depends(get_current_active_admin)
):
    """Kullanıcıyı sil (Soft Delete - Sadece Admin)"""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz.")
        
    user = await db.get(Kullanici, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
        
    # Soft delete (ELITE PRO approach)
    user.aktif = False
    db.add(user)
    await db.commit()
    logger.info(f"User soft-deleted: {user.kullanici_adi} by admin {current_admin.kullanici_adi}")
    return None
