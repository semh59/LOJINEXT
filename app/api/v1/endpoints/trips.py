from datetime import date, datetime, timezone
from typing import Annotated, Any, Dict, List, Optional


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
    get_current_user,
    get_sefer_service,
    require_permissions,
    get_background_job_manager,
)

from app.infrastructure.background.job_manager import BackgroundJobManager
from app.core.services.excel_service import ExcelService
from app.core.services.sefer_service import SeferService
from app.database.models import Kullanici
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.resilience.rate_limiter import RateLimiterDependency
from app.schemas.sefer import (
    SeferCreate,
    SeferResponse,
    SeferUpdate,
    SeferListResponse,
    SeferStatsResponse,
    SeferBulkStatusUpdate,
    SeferBulkCancel,
    SeferBulkResponse,
    SeferBulkDelete,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=SeferListResponse)
async def read_seferler(
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    service: SeferService = Depends(get_sefer_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    arac_id: Optional[int] = Query(None),
    sofor_id: Optional[int] = Query(None),
    durum: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """Seferleri listele (Service Layer)."""
    try:
        # Service handles skip/limit/safety/validation and ISOLATION internally
        # Returns Dict with "items", "total", "skip", "limit"
        return await service.get_all_paged(
            current_user=current_user,
            skip=skip,
            limit=limit,
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
            arac_id=arac_id,
            sofor_id=sofor_id,
            durum=durum,
            search=search,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing trips via service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Liste al?n?rken hata olu?tu")


@router.get("/today", response_model=SeferListResponse)
async def read_bugunun_seferleri(
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    service: SeferService = Depends(get_sefer_service),
):
    """BugÃ¼nÃ¼n seferlerini listele."""
    try:
        from datetime import date

        return await service.get_all_paged(
            current_user=current_user,
            baslangic_tarih=date.today().isoformat(),
            bitis_tarih=date.today().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error fetching today's trips: {e}")
        raise HTTPException(status_code=500, detail="BugÃ¼nkÃ¼ seferler alÄ±namadÄ±")


@router.get(
    "/excel/export",
    dependencies=[Depends(RateLimiterDependency("export_trips", rate=1.0, period=5.0))],
)
async def export_seferler(
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    service: SeferService = Depends(get_sefer_service),
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    arac_id: Optional[int] = Query(None),
    sofor_id: Optional[int] = Query(None),
    durum: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """Sefer listesini Excel olarak dÄ±ÅŸa aktar (Filtreli ve Limitli)."""
    try:
        MAX_EXPORT_LIMIT = 5000

        # Seferleri getir (MAX_EXPORT_LIMIT uygulanmis hali)
        seferler = await service.get_all_paged(
            current_user=current_user,
            skip=0,
            limit=MAX_EXPORT_LIMIT,
            aktif_only=False,
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
            arac_id=arac_id,
            sofor_id=sofor_id,
            durum=durum,
            search=search,
        )

        items = seferler.get("items", [])
        total = int((seferler.get("meta") or {}).get("total") or len(items))

        if total > MAX_EXPORT_LIMIT:
            raise ValueError(
                f"{MAX_EXPORT_LIMIT} satir limitini astiniz, tarih araligini daraltin."
            )

        data = []
        for s in items:
            d = s.model_dump() if hasattr(s, "model_dump") else s
            if getattr(s, "tarih", None):
                d["tarih"] = s.tarih.strftime("%Y-%m-%d")
            else:
                d["tarih"] = d.get("tarih", "")

            d["durum"] = getattr(s, "durum", d.get("durum"))
            d["plaka"] = getattr(s, "plaka", d.get("plaka", ""))
            d["sofor"] = getattr(s, "sofor_adi", d.get("sofor", ""))
            data.append(d)

        # Excel oluÅŸtur
        from fastapi import Response

        content = ExcelService.export_data(data, type="sefer_listesi")
        filename = (
            f"sefer_listesi_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.xlsx"
        )
        import urllib.parse

        encoded_filename = urllib.parse.quote(filename)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Excel export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SeferStatsResponse)
async def get_trip_stats(
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    service: SeferService = Depends(get_sefer_service),
    durum: Optional[str] = Query(None, description="Filtrelemek istenen sefer durumu"),
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    """
    Sefer istatistiklerini sunar.
    Tarih filtresi varsa dinamik sorgu kosturur, yoksa materialized view kullanir.
    """
    try:
        start_date = date.fromisoformat(baslangic_tarih) if baslangic_tarih else None
        end_date = date.fromisoformat(bitis_tarih) if bitis_tarih else None
    except ValueError:
        raise HTTPException(status_code=422, detail="Tarih formati gecersiz.")

    try:
        stats = await service.get_trip_stats(
            durum=durum,
            baslangic_tarih=start_date,
            bitis_tarih=end_date,
        )
        return SeferStatsResponse(**stats)
    except ValueError:
        raise HTTPException(status_code=422, detail="Gecersiz durum degeri.")
    except Exception as e:
        logger.error(f"Error fetching trip stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Sefer istatistikleri alinamadi.",
        )


@router.get("/analytics/fuel-performance")
async def get_fuel_performance_analytics(
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    service: SeferService = Depends(get_sefer_service),
    durum: Optional[str] = Query(None),
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    arac_id: Optional[int] = Query(None),
    sofor_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
):
    """
    Sefer bazli yakit performans metriklerini kullanici odakli payload ile doner.
    """
    try:
        start_date = date.fromisoformat(baslangic_tarih) if baslangic_tarih else None
        end_date = date.fromisoformat(bitis_tarih) if bitis_tarih else None
    except ValueError:
        raise HTTPException(status_code=422, detail="Tarih formati gecersiz.")

    try:
        return await service.get_fuel_performance_analytics(
            durum=durum,
            baslangic_tarih=start_date,
            bitis_tarih=end_date,
            arac_id=arac_id,
            sofor_id=sofor_id,
            search=search,
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="Gecersiz durum degeri.")
    except Exception as e:
        logger.error("Fuel performance analytics error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Yakit performansi alinamadi")


@router.post(
    "/",
    response_model=SeferResponse,
    status_code=201,
    dependencies=[Depends(RateLimiterDependency("create_trip", rate=2.0, period=1.0))],
)
async def create_sefer(
    sefer: SeferCreate,
    current_admin: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
):
    """Yeni sefer oluÅŸtur (Service Layer)."""
    try:
        logger.info(
            f"API: Creating trip with sefer_no: {sefer.sefer_no}, round_trip: {sefer.is_round_trip}"
        )
        sefer_id = await service.add_sefer(sefer, user_id=current_admin.id)
        logger.info(f"API: Service returned sefer_id: {sefer_id}")

        # Use service to get detailed object
        created_dict = await service.get_sefer_by_id(sefer_id)
        if not created_dict:
            logger.error(
                f"API: Created trip ID {sefer_id} could not be retrieved after creation"
            )
            raise HTTPException(
                status_code=500, detail="OluÅŸturulan kayÄ±t geri okunamadÄ±"
            )

        logger.info(f"API: Retrieved created trip dict for ID {sefer_id}")

        # Manually validate to SeferResponse to catch serialization errors
        from pydantic import ValidationError

        try:
            return SeferResponse.model_validate(created_dict)
        except ValidationError as ve:
            logger.error(
                f"API: Serialization error to SeferResponse for ID {sefer_id}: {ve}"
            )
            logger.error(f"API: Data causing error: {created_dict}")
            raise HTTPException(
                status_code=500,
                detail=f"Veri ÅŸema uyumsuzluÄŸu (ID:{sefer_id}): {str(ve.errors()[0].get('msg'))}",
            )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"API: Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        err_msg = f"API: Unexpected error creating trip: {str(e)}"
        logger.error(f"{err_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=err_msg)


@router.post("/{sefer_id}/return", response_model=SeferResponse, status_code=201)
async def create_return_trip(
    sefer_id: int,
    current_admin: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
):
    """Mevcut bir sefer baz alÄ±narak dÃ¶nÃ¼ÅŸ seferi oluÅŸtur (Backend mantÄ±ÄŸÄ±)."""
    try:
        new_sefer_id = await service.create_return_trip(
            sefer_id, user_id=current_admin.id
        )

        # Oku ve dÃ¶ndÃ¼r
        created_dict = await service.get_sefer_by_id(new_sefer_id)
        if not created_dict:
            raise HTTPException(
                status_code=500, detail="DÃ¶nÃ¼ÅŸ seferi oluÅŸturuldu ancak okunamadÄ±"
            )

        from pydantic import ValidationError

        try:
            return SeferResponse.model_validate(created_dict)
        except ValidationError as ve:
            logger.error(f"API: Serialization error to SeferResponse: {ve}")
            raise HTTPException(
                status_code=500, detail=f"Veri dÃ¶nÃ¼ÅŸÃ¼m hatasÄ±: {ve}"
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Return trip creation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="DÃ¶nÃ¼ÅŸ seferi oluÅŸturulurken hata meydana geldi"
        )


@router.get("/excel/template")
async def get_excel_template(
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
):
    """Sefer yÃ¼kleme iÃ§in Ã¶rnek Excel ÅŸablonu indir."""
    try:
        from app.core.services.excel_service import ExcelService

        content = ExcelService.generate_template(type="sefer")
        filename = "sefer_yukleme_sablonu.xlsx"

        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Error generating trip template: {e}")
        raise HTTPException(status_code=500, detail="Åablon oluÅŸturulamadÄ±")


@router.get("/{sefer_id}", response_model=SeferResponse)
async def read_sefer(
    sefer_id: int,
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    service: SeferService = Depends(get_sefer_service),
):
    """Tekil sefer getir (GÃ¼venli)."""
    sefer = await service.get_by_id(sefer_id, current_user=current_user)
    if not sefer:
        raise HTTPException(status_code=404, detail="Sefer bulunamadÄ±")
    return sefer


@router.get("/{sefer_id}/cost-analysis", response_model=dict, status_code=202)
async def analyze_trip_costs(
    sefer_id: int,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: SeferService = Depends(get_sefer_service),
    job_manager: BackgroundJobManager = Depends(get_background_job_manager),
):
    """
    Sefer maliyet analizi ve Smart Reconciliation tetikleme (Asenkron).
    """
    try:
        # Check permission (get_by_id handles ownership)
        sefer = await service.get_by_id(sefer_id, current_user=current_user)
        if not sefer:
            raise HTTPException(status_code=404, detail="Sefer bulunamadÄ±")

        # Submit to background job manager instead of raw BackgroundTasks
        job_id = await job_manager.submit(service.reconcile_costs, sefer_id)

        return {
            "status": "PROCESSING",
            "task_id": job_id,
            "message": "Maliyet analizi arka plana alÄ±ndÄ±. LÃ¼tfen durum sorgulama endpoint'ini kullanÄ±n.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Cost analysis initialization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Maliyet analizi baÅŸlatÄ±lamadÄ±")


@router.patch("/{sefer_id}", response_model=SeferResponse)
async def update_sefer(
    sefer_id: int,
    sefer_in: SeferUpdate,
    current_admin: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
):
    """Sefer gÃ¼ncelle (Service Layer)."""
    try:
        success = await service.update_sefer(
            sefer_id, sefer_in, user_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Sefer bulunamadÄ±")

        # GÃ¼ncel veriyi getir (Cache invalidation sonrasÄ± taze veri)
        updated = await service.get_sefer_by_id(sefer_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Guncellenen sefer bulunamadi")
        return updated

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="GÃ¼ncelleme sÄ±rasÄ±nda hata oluÅŸtu"
        )


@router.delete("/{sefer_id}", response_model=dict)
async def delete_sefer(
    sefer_id: int,
    current_admin: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
):
    """Seferi soft-delete olarak iptal eder."""

    try:
        success = await service.delete_sefer(sefer_id)
        if not success:
            raise HTTPException(
                status_code=404, detail="Sefer bulunamadÄ± veya silinemedi"
            )

        return {
            "status": "success",
            "message": "Sefer soft-delete olarak iptal edildi",
            "soft_deleted": True,
        }

    except Exception as e:
        logger.error(f"Error deleting trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Silme hatasÄ±")


@router.post(
    "/upload",
    response_model=dict,
    dependencies=[
        Depends(RateLimiterDependency("upload_trips", rate=1.0, period=10.0))
    ],
)
async def upload_sefer_excel(
    current_admin: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    file: UploadFile = File(...),
):
    # MIME Type Validation
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
    }
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Sadece Excel dosyalarÄ± (.xlsx, .xls) kabul edilir.",
        )

    # File extension validation
    if file.filename and not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Dosya uzantÄ±sÄ± .xlsx veya .xls olmalÄ±dÄ±r."
        )

    MAX_FILE_SIZE = 10 * 1024 * 1024

    # 1. Check Content-Length header (fast fail)
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Dosya boyutu 10MB'Ä± geÃ§emez.")

    # 2. Secure Read (Chunked) protecting RAM
    content = bytearray()
    chunk_size = 1024 * 1024  # 1MB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail="Dosya boyutu 10MB'Ä± geÃ§emez."
            )

    from app.services.api.sefer_import_service import get_sefer_import_service

    import_service = get_sefer_import_service()

    # Process using specialized service
    count, errors = await import_service.process_excel_import(
        bytes(content), current_admin.id
    )

    failed_count = len(errors)
    total_rows = count + failed_count

    return {
        "success": count > 0,
        "total_rows": total_rows,
        "success_count": count,
        "failed_count": failed_count,
        "errors": errors,
    }


@router.patch(
    "/bulk/status",
    response_model=SeferBulkResponse,
    dependencies=[Depends(RateLimiterDependency("bulk_status", rate=1.0, period=5.0))],
)
async def bulk_update_trip_status(
    data: SeferBulkStatusUpdate,
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
):
    """SeÃ§ili seferlerin durumunu toplu gÃ¼ncelle (SUPERVISOR+)."""
    return await service.bulk_update_status(
        data.sefer_ids, data.new_status, user_id=current_user.id
    )


@router.patch(
    "/bulk/cancel",
    response_model=SeferBulkResponse,
    dependencies=[Depends(RateLimiterDependency("bulk_cancel", rate=1.0, period=5.0))],
)
async def bulk_cancel_trips(
    data: SeferBulkCancel,
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
):
    """SeÃ§ili seferleri toplu iptal et (SUPERVISOR+)."""
    return await service.bulk_cancel(
        data.sefer_ids, data.iptal_nedeni, user_id=current_user.id
    )


@router.post("/bulk-delete", response_model=Dict[str, Any])
async def bulk_delete_trips(
    data: SeferBulkDelete,
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
) -> Any:
    """SeÃ§ilen seferleri toplu sil."""
    sefer_ids = data.sefer_ids
    logger.info(f"Bulk Delete Request: User={current_user.email}, IDs={sefer_ids}")
    if not sefer_ids:
        logger.warning("Bulk delete called with empty ID list")
        return {"success_count": 0, "failed_count": 0, "failed": []}
    return await service.bulk_delete(sefer_ids)


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    job_manager: BackgroundJobManager = Depends(get_background_job_manager),
):
    """
    Asenkron iÅŸlem durumunu kontrol eden polling endpointi.
    """
    status_info = job_manager.get_status(task_id)

    if status_info["status"] == "unknown":
        raise HTTPException(
            status_code=404, detail=f"'{task_id}' ID'li gÃ¶rev bulunamadÄ±."
        )

    # Normalize status for frontend (PROCESSING, SUCCESS, FAILED)
    norm_status = "PROCESSING"
    if status_info["status"] == "completed":
        norm_status = "SUCCESS"
    elif status_info["status"] == "failed":
        norm_status = "FAILED"

    return {
        "task_id": task_id,
        "status": norm_status,
        "result": status_info.get("result"),
        "error": status_info.get("error"),
        "timestamp": status_info.get("timestamp"),
    }


@router.get("/{sefer_id}/timeline")
async def get_sefer_timeline(
    sefer_id: int,
    current_user: Annotated[Kullanici, Depends(require_permissions("sefer:read"))],
    service: SeferService = Depends(get_sefer_service),
):
    """Seferin kronolojik olay akÄ±ÅŸÄ±nÄ± (audit log) getirir."""
    try:
        # Sefer var mÄ± kontrolÃ¼ (isolation/safety)
        await service.get_by_id(sefer_id, current_user=current_user)

        timeline_items = await service.get_timeline(sefer_id)
        return {"items": timeline_items}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching timeline for trip {sefer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Zaman Ã§izelgesi alÄ±namadÄ±")
