"""
LojiNext AI - Lokasyon (Güzergah) CRUD Endpoint'leri
Güzergah yönetimi için API - bayır, düzlük, mesafe bilgileri
"""

from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File

from app.api.deps import (
    UOWDep,
    get_current_active_admin,
    get_current_user,
    get_lokasyon_service,
)
from app.database.models import Kullanici, Lokasyon
from app.infrastructure.logging.logger import get_logger
from app.schemas.lokasyon import (
    LokasyonCreate,
    LokasyonPaginationResponse,
    LokasyonResponse,
    LokasyonUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/route-info")
async def get_route_info(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    cikis_lat: float = Query(..., description="Çıkış enlemi"),
    cikis_lon: float = Query(..., description="Çıkış boylamı"),
    varis_lat: float = Query(..., description="Varış enlemi"),
    varis_lon: float = Query(..., description="Varış boylamı"),
) -> Any:
    """
    Koordinatlara göre rota bilgilerini (mesafe, süre, iniş/çıkış) getirir.
    """
    from app.services.route_service import get_route_service

    route_service = get_route_service()
    route_details = await route_service.get_route_details(
        start_coords=(cikis_lon, cikis_lat),
        end_coords=(varis_lon, varis_lat),
        use_cache=True,
    )
    return route_details


@router.get("/", response_model=LokasyonPaginationResponse)
async def list_lokasyonlar(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    zorluk: Optional[str] = Query(
        None, description="Zorluk filtresi: Düz, Hafif Eğimli, Dik/Dağlık"
    ),
    search: Optional[str] = Query(None, description="Arama metni (Şehir, notlar)"),
    service: Annotated[Any, Depends(get_lokasyon_service)] = None,
):
    """Güzergahları listele (Service Layer)."""
    try:
        return await service.get_all_paged(
            skip=skip, limit=limit, zorluk=zorluk, search=search
        )
    except Exception as e:
        logger.error(f"Error listing locations: {e}")
        raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")


@router.post("/", response_model=LokasyonResponse, status_code=201)
async def create_lokasyon(
    lokasyon: LokasyonCreate,
    uow: UOWDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: Annotated[Any, Depends(get_lokasyon_service)] = None,
):
    """Yeni güzergah oluştur (Service Layer)."""
    try:
        lokasyon_id = await service.add_lokasyon(lokasyon)
        await uow.commit()
        # Fetch for response
        created = await uow.lokasyon_repo.get_by_id(lokasyon_id)
        return LokasyonResponse.model_validate(dict(created))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating location: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")


@router.get("/{lokasyon_id:int}", response_model=LokasyonResponse)
async def get_lokasyon(
    lokasyon_id: int,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: Annotated[Any, Depends(get_lokasyon_service)] = None,
):
    """Güzergah detayını getir."""
    loc = await service.repo.get_by_id(lokasyon_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Güzergah bulunamadı")
    return LokasyonResponse.model_validate(dict(loc))


@router.put("/{lokasyon_id:int}", response_model=LokasyonResponse)
async def update_lokasyon(
    lokasyon_id: int,
    lokasyon_in: LokasyonUpdate,
    uow: UOWDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: Annotated[Any, Depends(get_lokasyon_service)] = None,
):
    """Güzergah güncelle (Service Layer)."""
    try:
        success = await service.update_lokasyon(lokasyon_id, lokasyon_in)
        if not success:
            raise HTTPException(status_code=404, detail="Güzergah bulunamadı")
        await uow.commit()
        loc = await service.repo.get_by_id(lokasyon_id)
        return LokasyonResponse.model_validate(dict(loc))
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        raise HTTPException(status_code=500)


@router.delete("/{lokasyon_id:int}")
async def delete_lokasyon(
    lokasyon_id: int,
    uow: UOWDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    response: Response,
    service: Annotated[Any, Depends(get_lokasyon_service)] = None,
):
    """Güzergahı sil (Service: Smart Delete)."""

    current = await service.repo.get_by_id(lokasyon_id)
    if not current:
        raise HTTPException(status_code=404, detail="Güzergah bulunamadı")

    was_active = current.get("aktif", False)

    try:
        success = await service.delete_lokasyon(lokasyon_id)
        if not success:
            raise HTTPException(status_code=404)
        await uow.commit()

        if not was_active:
            response.headers["X-Delete-Type"] = "Hard Delete"

        return {
            "success": True,
            "deleted_id": lokasyon_id,
            "mode": "Hard" if not was_active else "Soft",
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting location: {e}")
        raise HTTPException(status_code=500)


@router.get("/search/by-route")
async def search_by_route(
    uow: UOWDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    cikis: str = Query(..., description="Çıkış yeri"),
    varis: str = Query(..., description="Varış yeri"),
):
    """Çıkış ve varış yerine göre güzergah ara."""
    # We can keep some specialized repo logic here but eventually move to service
    safe_cikis = cikis.replace("%", "\\%").replace("_", "\\_")
    safe_varis = varis.replace("%", "\\%").replace("_", "\\_")

    # Direct Repo access for specialized query is acceptable if no complex logic
    # But for deep audit, ideally service.search_paged()
    # Let's keep it simple for now as it's a GET search.
    from sqlalchemy import select

    stmt = select(Lokasyon).where(
        Lokasyon.cikis_yeri.ilike(f"%{safe_cikis}%"),
        Lokasyon.varis_yeri.ilike(f"%{safe_varis}%"),
    )
    result = await uow.session.execute(stmt)
    routes = result.scalars().all()

    return {
        "found": len(routes) > 0,
        "count": len(routes),
        "location": LokasyonResponse.model_validate(routes[0]) if routes else None,
        "routes": [LokasyonResponse.model_validate(r) for r in routes],
    }


@router.get("/unique-names", response_model=List[str])
async def get_unique_names(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    uow: UOWDep,
):
    """Benzersiz lokasyon isimlerini getir (Autocomplete)."""
    return await uow.lokasyon_repo.get_benzersiz_lokasyonlar()


@router.post("/{lokasyon_id:int}/analyze")
async def analyze_with_openroute(
    lokasyon_id: int,
    uow: UOWDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: Annotated[Any, Depends(get_lokasyon_service)] = None,
):
    """OpenRouteService kullanarak güzergahı analiz et (Service Layer)."""
    try:
        result = await service.analyze_route(lokasyon_id)
        await uow.commit()
        # Map hybrid results to frontend expectations
        return {
            "success": True,
            "api_mesafe_km": result.get("distance_km"),
            "api_sure_saat": round(result.get("duration_min", 0) / 60, 2),
            "ascent_m": result.get("ascent_m"),
            "descent_m": result.get("descent_m"),
            "otoban_mesafe_km": result.get("otoban_mesafe_km"),
            "sehir_ici_mesafe_km": result.get("sehir_ici_mesafe_km"),
            "source": result.get("source"),
            "is_corrected": result.get("is_corrected", False),
            "correction_reason": result.get("correction_reason"),
            "route_analysis": result.get("route_analysis") or result.get("details"),
            "elevation_profile": result.get("elevation_profile", []),
        }
    except Exception as e:
        logger.error(f"Error analyzing route: {e}")
        raise HTTPException(status_code=500, detail="Analiz başarısız")


@router.get("/excel/template")
async def get_excel_template(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """Güzergah yükleme şablonunu indir (Service Layer)."""
    from app.core.services.excel_service import ExcelService

    content = ExcelService.generate_template("guzergah")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=guzergah_yukleme_sablonu.xlsx"
        },
    )


@router.get("/excel/export")
async def export_locations(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: Annotated[Any, Depends(get_lokasyon_service)] = None,
):
    """Mevcut lokasyonları Excel olarak indir."""
    from app.core.services.excel_service import ExcelService

    data = await service.repo.get_all()

    content = ExcelService.export_data(data, type="lokasyon_listesi")

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=guzergahlar.xlsx"},
    )


@router.post("/upload")
async def upload_guzergahlar(
    file: UploadFile = File(...),
    current_user: Annotated[Kullanici, Depends(get_current_active_admin)] = None,
):
    """Excel ile toplu güzergah yükle (Service Layer)."""
    from app.core.services.import_service import get_import_service

    # Depends string referansı yerine doğrudan fonksiyonu çağırarak service alalım veya import düzeltelim
    service = get_import_service()

    content = await file.read()
    count, errors = await service.import_routes(content)
    return {"count": count, "errors": errors}
