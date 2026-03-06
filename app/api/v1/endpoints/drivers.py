import io
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import (
    SessionDep,
    get_current_active_admin,
    get_current_user,
    get_sofor_service,
)
from app.core.services.excel_service import ExcelService
from app.core.services.sofor_service import SoforService
from app.database.models import Kullanici, Sofor
from app.infrastructure.logging.logger import get_logger
from app.schemas.sofor import (
    DriverPerformanceSchema,
    SoforCreate,
    SoforResponse,
    SoforUpdate,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[SoforResponse])
async def read_soforler(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: SoforService = Depends(get_sofor_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    aktif_only: bool = Query(True, description="Sadece aktif şoförler"),
    search: Optional[str] = Query(None, description="İsim veya telefon araması"),
    ehliyet_sinifi: Optional[str] = Query(None, description="Ehliyet sınıfı"),
    min_score: Optional[float] = Query(None, ge=0.1, le=2.0),
    max_score: Optional[float] = Query(None, ge=0.1, le=2.0),
):
    try:
        # Service handles skip/limit/safety/validation internally
        return await service.get_all_paged(
            skip=skip,
            limit=limit,
            aktif_only=aktif_only,
            search=search,
            ehliyet_sinifi=ehliyet_sinifi,
            min_score=min_score,
            max_score=max_score,
        )
    except Exception as e:
        logger.error(f"Error listing drivers via service: {e}")
        raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")


@router.post("/", response_model=SoforResponse, status_code=201)
async def create_sofor(
    sofor: SoforCreate,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SoforService = Depends(get_sofor_service),
) -> Any:
    try:
        # Service handles duplicate check and reactivation of passive drivers
        sofor_id = await service.add_sofor(
            ad_soyad=sofor.ad_soyad,
            telefon=sofor.telefon,
            ehliyet_sinifi=sofor.ehliyet_sinifi,
            ise_baslama=sofor.ise_baslama,
            manual_score=sofor.manual_score,
            notlar=sofor.notlar,
        )
        # Fetch the created/updated object to return
        # Using DB session directly for fetch to ensure we return Pydantic-compatible DB model
        # (Service.get_by_id returns dict, we need ORM object for response_model usually
        # unless we change response_model to accept dict. SoforResponse works with dict too via from_attributes=True)

        # Safe approach: Fetch from DB using the ID
        created_sofor = await db.get(Sofor, sofor_id)
        if not created_sofor:
            # Should not happen
            raise HTTPException(
                status_code=500, detail="Sürücü oluşturuldu fakat geri getirilemedi."
            )

        logger.info(
            f"Driver processed via Service: {created_sofor.ad_soyad} by {current_admin.email}"
        )
        return created_sofor

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating driver: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")


@router.get("/excel/template")
async def download_template(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """Şoför yükleme için Excel şablonu indir"""
    template_data = ExcelService.generate_template("sofor")
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=sofor_yukleme_sablonu.xlsx"
        },
    )


@router.get("/excel/export")
async def export_drivers(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: SoforService = Depends(get_sofor_service),
    aktif_only: bool = Query(True, description="Sadece aktif şoförler"),
    search: Optional[str] = Query(None, description="İsim veya telefon araması"),
    ehliyet_sinifi: Optional[str] = Query(None, description="Ehliyet sınıfı"),
    min_score: Optional[float] = Query(None, ge=0.1, le=2.0),
    max_score: Optional[float] = Query(None, ge=0.1, le=2.0),
):
    """Mevcut şoförleri Excel olarak indir (Filtreli & Kurumsal Format)"""
    try:
        # Tüm listeyi çek (limit yüksek)
        drivers = await service.get_all_paged(
            skip=0,
            limit=10000,
            aktif_only=aktif_only,
            search=search,
            ehliyet_sinifi=ehliyet_sinifi,
            min_score=min_score,
            max_score=max_score,
        )

        # Service zaten Dict listesi döndürüyor, doğrudan kullan
        # Hassas verileri temizle (PII koruması)
        clean_data = []
        for d in drivers:
            clean_item = {
                "id": d.get("id"),
                "ad_soyad": d.get("ad_soyad"),
                "ehliyet_sinifi": d.get("ehliyet_sinifi", "E"),
                "ise_baslama": d.get("ise_baslama"),
                "score": d.get("score", 1.0),
                "manual_score": d.get("manual_score", 1.0),
                "aktif": "Aktif" if d.get("aktif") else "Pasif",
            }
            clean_data.append(clean_item)

        # Excel oluştur
        content = ExcelService.export_data(clean_data, type="sofor_listesi")

        filename = (
            f"sofor_listesi_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.xlsx"
        )

        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Error exporting drivers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Excel oluşturulurken hata oluştu")


@router.post("/excel/upload")
async def upload_drivers(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    file: UploadFile = File(...),
):
    """Excel'den toplu şoför yükle"""
    from app.core.services.import_service import get_import_service

    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
    }
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, detail="Sadece Excel dosyaları kabul edilir."
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Dosya boyutu 10MB'ı geçemez.")

    import_service = get_import_service()
    created_count, errors = await import_service.process_driver_import(content)

    return {
        "status": "success",
        "message": f"{created_count} şoför yüklendi.",
        "errors": errors,
    }


@router.get("/{sofor_id}", response_model=SoforResponse)
async def read_sofor(
    sofor_id: int,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    sofor = await db.get(Sofor, sofor_id)
    if not sofor:
        raise HTTPException(status_code=404, detail="Şoför bulunamadı")
    return sofor


@router.get("/{sofor_id}/performance", response_model=DriverPerformanceSchema)
async def get_driver_performance(
    sofor_id: int,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: SoforService = Depends(get_sofor_service),
):
    """
    Sürücü performans karnesini getir (AI Analizli)
    """
    # Check existence
    sofor = await db.get(Sofor, sofor_id)
    if not sofor:
        raise HTTPException(status_code=404, detail="Şoför bulunamadı")

    try:
        performance = await service.get_performance_details(sofor_id)
        return performance
    except Exception as e:
        logger.error(f"Error fetching driver performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Performans verileri alınamadı")


@router.put("/{sofor_id}", response_model=SoforResponse)
async def update_sofor(
    sofor_id: int,
    sofor_in: SoforUpdate,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SoforService = Depends(get_sofor_service),
):
    try:
        # Convert Pydantic to dict, excluding unset
        update_data = sofor_in.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=400, detail="Güncellenecek veri gönderilmedi"
            )

        success = await service.update_sofor(sofor_id, **update_data)
        if not success:
            raise HTTPException(
                status_code=404, detail="Şoför bulunamadı veya güncellenemedi"
            )

        # Fetch updated
        updated_sofor = await db.get(Sofor, sofor_id)
        return updated_sofor

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating driver: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")


@router.delete("/{sofor_id}", response_model=Dict)
async def delete_sofor(
    sofor_id: int,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SoforService = Depends(get_sofor_service),
):
    # Check status to determine message
    sofor = await db.get(Sofor, sofor_id)
    if not sofor:
        raise HTTPException(status_code=404, detail="Şoför bulunamadı")

    was_active = sofor.aktif

    try:
        # Service handles 'Smart Delete' (Soft delete)
        success = await service.delete_sofor(sofor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Şoför bulunamadı")

        msg = "Şoför pasife çekildi" if was_active else "Şoför tamamen silindi"
        logger.info(f"Delete action for {sofor_id}: {msg}")

        return {"status": "success", "message": msg}

    except Exception as e:
        logger.error(f"Error deleting driver: {e}", exc_info=True)
        # Check if it was an integrity error (raised as ValueError by service)
        if "sefer kayıtları" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=500, detail="Silme işlemi başarısız")


@router.delete("/bulk", response_model=Dict)
async def bulk_delete_soforler(
    ids: List[int],
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SoforService = Depends(get_sofor_service),
):
    """Toplu şoför silme (Soft Delete & Optimized Transaction)."""
    if not ids:
        raise HTTPException(status_code=400, detail="Silinecek ID listesi boş olamaz")

    if len(ids) > 100:
        raise HTTPException(
            status_code=400, detail="Tek seferde en fazla 100 kayıt silinebilir"
        )

    try:
        # Service handles multi-item update in a single UoW
        result = await service.bulk_delete(ids)

        logger.info(
            f"Bulk delete completed: {result['deleted']} drivers deleted by {current_admin.email}"
        )
        return result

    except Exception as e:
        logger.error(f"Error in bulk delete API: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Toplu silme işlemi sırasında hata oluştu"
        )


@router.post("/{sofor_id}/score", response_model=SoforResponse)
async def update_driver_score(
    sofor_id: int,
    score: float,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SoforService = Depends(get_sofor_service),
):
    try:
        # Service handles validation (0.1-2.0) and existence check
        success = await service.update_score(sofor_id, score)
        if not success:
            raise HTTPException(
                status_code=404, detail="Şoför bulunamadı veya puan güncellenemedi"
            )

        # Fetch updated to return response
        updated_sofor = await db.get(Sofor, sofor_id)
        return updated_sofor

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating score via service: {e}")
        raise HTTPException(status_code=500, detail="Puan güncellenirken sunucu hatası")
