"""
LojiNext AI - Lokasyon (Güzergah) CRUD Endpoint'leri
Güzergah yönetimi için API - bayır, düzlük, mesafe bilgileri
"""

from datetime import datetime
from typing import List, Optional, Annotated

from app.api.deps import SessionDep, get_current_user, get_current_active_admin
from app.database.models import Lokasyon, Kullanici
from app.schemas.lokasyon import LokasyonCreate, LokasyonUpdate, LokasyonResponse
from app.core.services.lokasyon_service import get_lokasyon_service
from fastapi import APIRouter, HTTPException, Query, Depends, Response

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/", response_model=List[LokasyonResponse])
async def list_lokasyonlar(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    zorluk: Optional[str] = Query(None, description="Zorluk filtresi: Düz, Hafif Eğimli, Dik/Dağlık"),
    search: Optional[str] = Query(None, description="Arama metni (Şehir, notlar)")
):
    """Güzergahları listele (Service Layer)."""
    service = get_lokasyon_service()
    try:
        return await service.get_all_paged(
            skip=skip,
            limit=limit,
            zorluk=zorluk,
            search=search
        )
    except Exception as e:
        logger.error(f"Error listing locations: {e}")
        raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")

@router.post("/", response_model=LokasyonResponse)
async def create_lokasyon(
    lokasyon: LokasyonCreate, 
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Yeni güzergah oluştur (Service Layer)."""
    service = get_lokasyon_service()
    try:
        lokasyon_id = await service.add_lokasyon(lokasyon)
        # Fetch for response
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        repo = get_lokasyon_repo()
        created = await repo.get_by_id(lokasyon_id)
        return LokasyonResponse.model_validate(dict(created))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating location: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")

@router.get("/{lokasyon_id}", response_model=LokasyonResponse)
async def get_lokasyon(
    lokasyon_id: int, 
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """Güzergah detayını getir."""
    service = get_lokasyon_service()
    loc = await service.repo.get_by_id(lokasyon_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Güzergah bulunamadı")
    return LokasyonResponse.model_validate(dict(loc))

@router.put("/{lokasyon_id}", response_model=LokasyonResponse)
async def update_lokasyon(
    lokasyon_id: int, 
    lokasyon_in: LokasyonUpdate, 
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Güzergah güncelle (Service Layer)."""
    service = get_lokasyon_service()
    try:
        success = await service.update_lokasyon(lokasyon_id, lokasyon_in)
        if not success:
            raise HTTPException(status_code=404, detail="Güzergah bulunamadı")
        loc = await service.repo.get_by_id(lokasyon_id)
        return LokasyonResponse.model_validate(dict(loc))
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        raise HTTPException(status_code=500)

@router.delete("/{lokasyon_id}")
async def delete_lokasyon(
    lokasyon_id: int, 
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    response: Response
):
    """Güzergahı sil (Service: Smart Delete)."""
    service = get_lokasyon_service()
    
    current = await service.repo.get_by_id(lokasyon_id)
    if not current:
        raise HTTPException(status_code=404, detail="Güzergah bulunamadı")
        
    was_active = current.get('aktif', False)
    
    try:
        success = await service.delete_lokasyon(lokasyon_id)
        if not success:
            raise HTTPException(status_code=404)
            
        if not was_active:
            response.headers["X-Delete-Type"] = "Hard Delete"
            
        return {"success": True, "deleted_id": lokasyon_id, "mode": "Hard" if not was_active else "Soft"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting location: {e}")
        raise HTTPException(status_code=500)

@router.get("/search/by-route")
async def search_by_route(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    cikis: str = Query(..., description="Çıkış yeri"),
    varis: str = Query(..., description="Varış yeri")
):
    """Çıkış ve varış yerine göre güzergah ara."""
    from app.database.repositories.lokasyon_repo import get_lokasyon_repo
    repo = get_lokasyon_repo()
    
    # We can keep some specialized repo logic here but eventually move to service
    safe_cikis = cikis.replace("%", "\\%").replace("_", "\\_")
    safe_varis = varis.replace("%", "\\%").replace("_", "\\_")
    
    # Direct Repo access for specialized query is acceptable if no complex logic
    # But for deep audit, ideally service.search_paged()
    # Let's keep it simple for now as it's a GET search.
    async with repo._get_session() as session:
        from sqlalchemy import select
        stmt = select(Lokasyon).where(
            Lokasyon.cikis_yeri.ilike(f"%{safe_cikis}%"),
            Lokasyon.varis_yeri.ilike(f"%{safe_varis}%")
        )
        result = await session.execute(stmt)
        routes = result.scalars().all()

    return {
        "found": len(routes) > 0,
        "count": len(routes),
        "location": LokasyonResponse.model_validate(routes[0]) if routes else None,
        "routes": [LokasyonResponse.model_validate(r) for r in routes]
    }

@router.get("/unique-names", response_model=List[str])
async def get_unique_names(
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """Benzersiz lokasyon isimlerini getir (Autocomplete)."""
    from app.database.repositories.lokasyon_repo import get_lokasyon_repo
    repo = get_lokasyon_repo()
    return await repo.get_benzersiz_lokasyonlar()

@router.post("/{lokasyon_id}/analyze")
async def analyze_with_openroute(
    lokasyon_id: int, 
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """OpenRouteService kullanarak güzergahı analiz et (Service Layer)."""
    service = get_lokasyon_service()
    try:
        result = await service.analyze_route(lokasyon_id)
        return {
            "success": True,
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing route: {e}")
        raise HTTPException(status_code=500, detail="Analiz başarısız")
