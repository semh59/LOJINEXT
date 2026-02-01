from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user
from app.core.services.guzergah_service import get_guzergah_service, GuzergahService
from app.schemas.guzergah import GuzergahCreate, GuzergahUpdate, GuzergahResponse

router = APIRouter()

@router.get("/", response_model=List[GuzergahResponse])
async def get_guzergahlar(
    service: GuzergahService = Depends(get_guzergah_service),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """Tüm aktif güzergahları getir"""
    return await service.get_all_active()

@router.post("/", response_model=GuzergahResponse)
async def create_guzergah(
    data: GuzergahCreate,
    service: GuzergahService = Depends(get_guzergah_service),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """Yeni güzergah oluştur"""
    return await service.create_guzergah(data)

@router.put("/{id}", response_model=bool)
async def update_guzergah(
    id: int,
    data: GuzergahUpdate,
    service: GuzergahService = Depends(get_guzergah_service),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """Güzergah güncelle"""
    return await service.update_guzergah(id, data)

@router.delete("/{id}", response_model=bool)
async def delete_guzergah(
    id: int,
    service: GuzergahService = Depends(get_guzergah_service),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """Güzergah sil (Soft delete)"""
    return await service.delete_guzergah(id)
