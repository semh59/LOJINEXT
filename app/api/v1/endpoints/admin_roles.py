from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.infrastructure.security.permission_checker import require_yetki
from app.database.models import Rol, Kullanici
from app.schemas.user import RolRead
from app.infrastructure.logging.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=List[RolRead])
async def get_roles(
    db: SessionDep, current_user: Kullanici = Depends(require_yetki("rol_oku"))
):
    """Sistem rollerini listele"""
    stmt = select(Rol).order_by(Rol.ad)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{role_id}", response_model=RolRead)
async def get_role(
    role_id: int,
    db: SessionDep,
    current_user: Kullanici = Depends(require_yetki("rol_oku")),
):
    """Spesifik bir rol getir"""
    role = await db.get(Rol, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol bulunamadı")
    return role


@router.post("/", response_model=RolRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    ad: str,
    yetkiler: dict,
    db: SessionDep,
    current_user: Kullanici = Depends(require_yetki("rol_yaz")),
):
    """Yeni rol oluştur"""
    # Check if exists
    stmt = select(Rol).where(Rol.ad == ad)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu isimde bir rol zaten var")

    role = Rol(ad=ad, yetkiler=yetkiler)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role
