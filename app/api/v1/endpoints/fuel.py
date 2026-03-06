from datetime import date, datetime
from typing import Annotated, Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from app.api.deps import (
    SessionDep,
    get_current_active_admin,
    get_current_user,
    get_yakit_service,
)
from app.core.services.yakit_service import YakitService
from app.database.models import Kullanici, YakitAlimi
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.resilience.rate_limiter import RateLimiterDependency
from app.schemas.yakit import YakitCreate, YakitListResponse, YakitResponse, YakitUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_fuel_stats(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: YakitService = Depends(get_yakit_service),
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    """
    Yakıt istatistiklerini getir (Service Layer).
    """
    # Tarih parsing
    try:
        start_date = None
        if baslangic_tarih:
            start_date = datetime.strptime(baslangic_tarih, "%Y-%m-%d").date()

        end_date = None
        if bitis_tarih:
            end_date = datetime.strptime(bitis_tarih, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Geçersiz tarih formatı. YYYY-MM-DD kullanın."
        )

    try:
        return await service.get_stats(baslangic_tarih=start_date, bitis_tarih=end_date)
    except Exception as e:
        logger.error(f"Error getting fuel stats: {e}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı")


# read_yakit_alimlari wrapped in try/except


@router.get("/", response_model=YakitListResponse)
async def read_yakit_alimlari(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: YakitService = Depends(get_yakit_service),
    baslangic_tarih: Optional[str] = Query(None),
    bitis_tarih: Optional[str] = Query(None),
    arac_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = 20,
) -> Any:
    """Yakıt alımlarını listele (Service Layer)."""
    try:
        # Service handles skip/limit/safety/validation internally
        return await service.get_all_paged(
            skip=skip,
            limit=limit,
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
            arac_id=arac_id,
        )
    except Exception as e:
        logger.error(f"Error listing fuel via service: {e}")
        raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")


@router.post(
    "/",
    response_model=YakitResponse,
    status_code=201,
    dependencies=[Depends(RateLimiterDependency("create_fuel", rate=2.0, period=1.0))],
)
async def create_yakit(
    yakit: YakitCreate,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: YakitService = Depends(get_yakit_service),
):
    """Yeni yakıt alımı ekle (Service Layer)."""
    try:
        yakit_id = await service.add_yakit(yakit)
        return await service.get_yakit_by_id(yakit_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating fuel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")


@router.get("/{yakit_id}", response_model=YakitResponse)
async def read_yakit(
    yakit_id: int,
    service: YakitService = Depends(get_yakit_service),
    current_user: Annotated[Kullanici, Depends(get_current_user)] = None,
):
    """Yakıt alımı detaylarını getir (Service Layer)."""
    yakit = await service.get_yakit_by_id(yakit_id)
    if not yakit:
        raise HTTPException(status_code=404, detail="Yakıt alımı bulunamadı")
    return yakit


@router.put("/{yakit_id}", response_model=YakitResponse)
async def update_yakit(
    yakit_id: int,
    yakit_in: YakitUpdate,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: YakitService = Depends(get_yakit_service),
):
    """Yakıt kaydı güncelle (Service Layer)."""
    try:
        success = await service.update_yakit(yakit_id, yakit_in)
        if not success:
            raise HTTPException(status_code=404, detail="Yakıt alımı bulunamadı")

        return await service.get_yakit_by_id(yakit_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Güncelleme hatası")


@router.delete("/{yakit_id}", response_model=YakitResponse)
async def delete_yakit(
    yakit_id: int,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: YakitService = Depends(get_yakit_service),
    response: Response = None,
):
    """Yakıt alımı sil (Service: Smart Delete)."""

    current = await db.get(YakitAlimi, yakit_id)
    if not current:
        raise HTTPException(status_code=404, detail="Yakıt alımı bulunamadı")

    was_active = current.aktif

    try:
        success = await service.delete_yakit(yakit_id)
        if not success:
            raise HTTPException(status_code=404, detail="Silinemedi")

        if was_active:
            # Soft Deleted
            updated = await db.get(YakitAlimi, yakit_id)
            return updated
        else:
            # Hard Deleted
            response.headers["X-Delete-Type"] = "Hard Delete"
            return current

    except Exception as e:
        logger.error(f"Error deleting fuel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Silme hatası")


@router.get("/excel/export")
async def export_yakit_alimlari(
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: YakitService = Depends(get_yakit_service),
    baslangic_tarih: Optional[str] = Query(None),
    bitis_tarih: Optional[str] = Query(None),
    arac_id: Optional[int] = Query(None),
):
    """Yakıt alımlarını Excel olarak dışa aktar."""
    try:
        # Get all matching records (not paged)
        data = await service.get_all_paged(
            skip=0,
            limit=10000,  # Large enough for export
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
            arac_id=arac_id,
        )

        # Convert Pydantic models to dicts
        clean_data = [d.model_dump() for d in data]

        # Excel oluştur
        from app.core.services.excel_service import ExcelService

        content = ExcelService.export_data(clean_data, type="yakit_listesi")

        filename = f"yakit_raporu_{date.today().isoformat()}.xlsx"
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Error exporting fuel: {e}")
        raise HTTPException(status_code=500, detail="Excel oluşturulurken hata oluştu")


@router.get("/excel/template")
async def get_fuel_excel_template(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
):
    """Yakıt yükleme şablonu indir."""
    from app.core.services.excel_service import ExcelService

    try:
        content = ExcelService.generate_template("yakit")
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=yakit_yukleme_sablonu.xlsx"
            },
        )
    except Exception as e:
        logger.error(f"Error generating fuel template: {e}")
        raise HTTPException(status_code=500, detail="Şablon oluşturulamadı")


@router.post("/excel/upload", response_model=dict)
async def upload_yakit_excel(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    file: UploadFile = File(...),
):
    """
    Excel dosyasından toplu yakıt fişi yükleme (ImportService kullanarak).
    Logic sızıntısı ve N+1 giderildi.
    """
    from app.core.services.import_service import get_import_service

    # MIME Type Validation
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
    }
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, detail="Sadece Excel dosyaları (.xlsx, .xls) kabul edilir."
        )

    # File extension validation
    if file.filename and not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Dosya uzantısı .xlsx veya .xls olmalıdır."
        )

    MAX_FILE_SIZE = 10 * 1024 * 1024

    # 1. Check Content-Length header (fast fail)
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Dosya boyutu 10MB'ı geçemez.")

    # 2. Secure Read (Chunked) protecting RAM
    content = bytearray()
    chunk_size = 1024 * 1024  # 1MB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Dosya boyutu 10MB'ı geçemez.")

    import_service = get_import_service()

    count, errors = await import_service.process_yakit_import(bytes(content))

    return {
        "status": "success" if not errors else "partial_success",
        "processed": count,
        "saved": count,
        "errors": errors,
    }
