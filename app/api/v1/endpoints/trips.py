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

from sqlalchemy import text
from app.api.deps import (
    SessionDep,
    get_current_active_admin,
    get_current_active_user,
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
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=SeferListResponse)
async def read_seferler(
    db: SessionDep,
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
    except Exception as e:
        logger.error(f"Error listing trips via service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")


@router.get("/today", response_model=SeferListResponse)
async def read_bugunun_seferleri(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: SeferService = Depends(get_sefer_service),
):
    """Bugünün seferlerini listele."""
    try:
        from datetime import date

        return await service.get_all_paged(
            current_user=current_user,
            baslangic_tarih=date.today().isoformat(),
            bitis_tarih=date.today().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error fetching today's trips: {e}")
        raise HTTPException(status_code=500, detail="Bugünkü seferler alınamadı")


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
    """Sefer listesini Excel olarak dışa aktar (Filtreli ve Limitli)."""
    try:
        from fastapi.responses import StreamingResponse

        MAX_EXPORT_LIMIT = 5000

        # Seferleri getir (MAX_EXPORT_LIMIT uygulanmış hali)
        seferler = await service.get_all_paged(
            current_user=current_user,
            skip=0,
            limit=MAX_EXPORT_LIMIT + 1,  # 1 fazlasını sor ki limiti aştığını anlayalım
            aktif_only=False,
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
            arac_id=arac_id,
            sofor_id=sofor_id,
            durum=durum,
            search=search,
        )

        items = seferler.get("items", [])

        if len(items) > MAX_EXPORT_LIMIT:
            raise ValueError(
                f"{MAX_EXPORT_LIMIT} satır limitini aştınız, tarih aralığını daraltın."
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

        # Excel oluştur
        from fastapi import Response

        content = ExcelService.export_data(data, type="sefer_listesi")
        filename = (
            f"sefer_listesi_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.xlsx"
        )
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Excel export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SeferStatsResponse)
async def get_trip_stats(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    durum: Optional[str] = Query(None, description="Filtrelemek istenen sefer durumu"),
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    """
    Sefer istatistiklerini sunar.
    Tarih filtresi varsa dinamik sorgu koşturur, yoksa Materialized View kullanır.
    """
    try:
        # Dinamik filtreleme gerekip gerekmediğini kontrol et
        use_dynamic = bool(baslangic_tarih or bitis_tarih)

        if use_dynamic:
            # Doğrudan tablodan (Index-based) SUM/COUNT yap
            where_clauses = ["is_real = TRUE", "is_deleted = FALSE", "durum != 'İptal'"]
            params = {}

            if durum:
                where_clauses.append("durum = :durum")
                params["durum"] = durum
            if baslangic_tarih:
                where_clauses.append("tarih >= :start")
                params["start"] = baslangic_tarih
            if bitis_tarih:
                where_clauses.append("tarih <= :end")
                params["end"] = bitis_tarih

            where_stmt = " AND ".join(where_clauses)
            query = text(f"""
                SELECT 
                    COUNT(id) as toplam_sefer, 
                    SUM(mesafe_km) as toplam_km, 
                    SUM(otoban_mesafe_km) as highway_km, 
                    SUM(ascent_m) as total_ascent, 
                    SUM(net_kg / 1000.0) as total_weight,
                    MAX(created_at) as last_updated
                FROM seferler
                WHERE {where_stmt}
            """)
        else:
            # Performans için MV kullan
            if durum:
                query = text(
                    "SELECT toplam_sefer, toplam_km, highway_km, total_ascent, total_weight, last_updated FROM sefer_istatistik_mv WHERE durum = :durum"
                )
                params = {"durum": durum}
            else:
                query = text("""
                    SELECT 
                        SUM(toplam_sefer) as toplam_sefer, 
                        SUM(toplam_km) as toplam_km, 
                        SUM(highway_km) as highway_km, 
                        SUM(total_ascent) as total_ascent, 
                        SUM(total_weight) as total_weight,
                        MAX(last_updated) as last_updated
                    FROM sefer_istatistik_mv
                """)
                params = {}

        result = await db.execute(query, params)
        row = result.fetchone()

        if not row or not row.toplam_sefer:
            return SeferStatsResponse()

        avg_highway_pct = 0
        t_km = float(row.toplam_km or 0)
        h_km = float(row.highway_km or 0)
        if t_km > 0:
            avg_highway_pct = int(round((h_km / t_km) * 100))

        return SeferStatsResponse(
            toplam_sefer=int(row.toplam_sefer) if row.toplam_sefer else 0,
            toplam_km=t_km,
            highway_km=h_km,
            total_ascent=float(row.total_ascent or 0.0),
            total_weight=float(row.total_weight or 0.0),
            avg_highway_pct=avg_highway_pct,
            last_updated=row.last_updated,
        )
    except Exception as e:
        logger.error(f"Error fetching trip stats: {e}", exc_info=True)
        return SeferStatsResponse()


@router.post(
    "/",
    response_model=SeferResponse,
    status_code=201,
    dependencies=[Depends(RateLimiterDependency("create_trip", rate=2.0, period=1.0))],
)
async def create_sefer(
    sefer: SeferCreate,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SeferService = Depends(get_sefer_service),
):
    """Yeni sefer oluştur (Service Layer)."""
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
                status_code=500, detail="Oluşturulan kayıt geri okunamadı"
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
                detail=f"Veri şema uyumsuzluğu (ID:{sefer_id}): {str(ve.errors()[0].get('msg'))}",
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
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SeferService = Depends(get_sefer_service),
):
    """Mevcut bir sefer baz alınarak dönüş seferi oluştur (Backend mantığı)."""
    try:
        new_sefer_id = await service.create_return_trip(
            sefer_id, user_id=current_admin.id
        )

        # Oku ve döndür
        created_dict = await service.get_sefer_by_id(new_sefer_id)
        if not created_dict:
            raise HTTPException(
                status_code=500, detail="Dönüş seferi oluşturuldu ancak okunamadı"
            )

        from pydantic import ValidationError

        try:
            return SeferResponse.model_validate(created_dict)
        except ValidationError as ve:
            logger.error(f"API: Serialization error to SeferResponse: {ve}")
            raise HTTPException(status_code=500, detail=f"Veri dönüşüm hatası: {ve}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Return trip creation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Dönüş seferi oluşturulurken hata meydana geldi"
        )


@router.get("/excel/template")
async def get_excel_template(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """Sefer yükleme için örnek Excel şablonu indir."""
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
        raise HTTPException(status_code=500, detail="Şablon oluşturulamadı")


@router.get("/{sefer_id}", response_model=SeferResponse)
async def read_sefer(
    sefer_id: int,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: SeferService = Depends(get_sefer_service),
):
    """Tekil sefer getir (Güvenli)."""
    sefer = await service.get_by_id(sefer_id, current_user=current_user)
    if not sefer:
        raise HTTPException(status_code=404, detail="Sefer bulunamadı")
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
            raise HTTPException(status_code=404, detail="Sefer bulunamadı")

        # Submit to background job manager instead of raw BackgroundTasks
        job_id = await job_manager.submit(service.reconcile_costs, sefer_id)

        return {
            "status": "PROCESSING",
            "task_id": job_id,
            "message": "Maliyet analizi arka plana alındı. Lütfen durum sorgulama endpoint'ini kullanın.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Cost analysis initialization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Maliyet analizi başlatılamadı")


@router.patch("/{sefer_id}", response_model=SeferResponse)
async def update_sefer(
    sefer_id: int,
    sefer_in: SeferUpdate,
    current_admin: Annotated[Kullanici, Depends(require_permissions("sefer:write"))],
    service: SeferService = Depends(get_sefer_service),
):
    """Sefer güncelle (Service Layer)."""
    try:
        success = await service.update_sefer(
            sefer_id, sefer_in, user_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Sefer bulunamadı")

        # Güncel veriyi getir (Cache invalidation sonrası taze veri)
        return await service.get_sefer_by_id(sefer_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Güncelleme sırasında hata oluştu")


@router.delete("/{sefer_id}", response_model=dict)
async def delete_sefer(
    sefer_id: int,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: SeferService = Depends(get_sefer_service),
):
    """Sefer sil (Hard Delete)."""

    try:
        success = await service.delete_sefer(sefer_id)
        if not success:
            raise HTTPException(
                status_code=404, detail="Sefer bulunamadı veya silinemedi"
            )

        return {"status": "success", "message": "Sefer tamamen silindi"}

    except Exception as e:
        logger.error(f"Error deleting trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Silme hatası")


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
    """Seçili seferlerin durumunu toplu güncelle (SUPERVISOR+)."""
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
    """Seçili seferleri toplu iptal et (SUPERVISOR+)."""
    return await service.bulk_cancel(
        data.sefer_ids, data.iptal_nedeni, user_id=current_user.id
    )


@router.post("/bulk-delete", response_model=Dict[str, Any])
async def bulk_delete_trips(
    sefer_ids: List[int],
    current_user: Kullanici = Depends(get_current_active_user),
    service: SeferService = Depends(get_sefer_service),
) -> Any:
    """Seçilen seferleri toplu sil."""
    logger.info(f"Bulk Delete Request: User={current_user.username}, IDs={sefer_ids}")
    if not sefer_ids:
        logger.warning("Bulk delete called with empty ID list")
        return {"success_count": 0, "failed_count": 0, "failed": []}
    return await service.bulk_delete(sefer_ids)


@router.get("/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: Annotated[Kullanici, Depends(get_current_user)] = None,
    job_manager: BackgroundJobManager = Depends(get_background_job_manager),
):
    """
    Asenkron işlem durumunu kontrol eden polling endpointi.
    """
    status_info = job_manager.get_status(task_id)

    if status_info["status"] == "unknown":
        raise HTTPException(
            status_code=404, detail=f"'{task_id}' ID'li görev bulunamadı."
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
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: SeferService = Depends(get_sefer_service),
):
    """Seferin kronolojik olay akışını (audit log) getirir."""
    try:
        # Sefer var mı kontrolü (isolation/safety)
        await service.get_by_id(sefer_id)

        from app.database.unit_of_work import UnitOfWork

        async with UnitOfWork() as uow:
            logs = await uow.audit_repo.get_sefer_timeline(sefer_id)

            # Timeline için normalize et
            timeline = []
            for log in logs:
                timeline.append(
                    {
                        "id": log.id,
                        "zaman": log.zaman,
                        "aksiyon": log.aksiyon_tipi,
                        "aciklama": log.aciklama,
                        "degisen_alanlar": log.yeni_deger.keys()
                        if log.yeni_deger
                        else [],
                        "kullanici": log.kullanici_email or "Sistem",
                    }
                )

            return {"items": timeline}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching timeline for trip {sefer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Zaman çizelgesi alınamadı")
