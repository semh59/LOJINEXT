from typing import List, Annotated, Optional

from app.api.deps import SessionDep, get_current_user, get_current_active_admin
from app.database.models import Sefer, Kullanici
from app.schemas.sefer import SeferCreate, SeferResponse, SeferUpdate
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy import select

from app.infrastructure.logging.logger import get_logger
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, Query, Response

from app.core.services.sefer_service import get_sefer_service

logger = get_logger(__name__)
router = APIRouter()

# read_seferler stays same for now (filtering logic) but wrapped in try/except ideally.

@router.get("/", response_model=List[SeferResponse])
async def read_seferler(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    arac_id: Optional[int] = Query(None),
    sofor_id: Optional[int] = Query(None),
    durum: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Seferleri listele (Service Layer)."""
    service = get_sefer_service()
    try:
        # Service handles skip/limit/safety/validation internally
         return await service.get_all_paged(
             skip=skip, 
             limit=limit,
             baslangic_tarih=baslangic_tarih,
             bitis_tarih=bitis_tarih,
             arac_id=arac_id,
             sofor_id=sofor_id,
             durum=durum,
             search=search
         )
    except Exception as e:
         logger.error(f"Error listing trips via service: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")

@router.get("/excel/export")
async def export_seferler(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    baslangic_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    bitis_tarih: Optional[str] = Query(None, description="YYYY-MM-DD"),
    arac_id: Optional[int] = Query(None),
    sofor_id: Optional[int] = Query(None),
    durum: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Sefer listesini Excel olarak dışa aktar (Filtreli)."""
    service = get_sefer_service()
    from app.core.services.excel_service import ExcelService
    import io
    from datetime import datetime
    
    try:
        # Seferleri getir (Limitsiz export için yüksek limit)
        seferler = await service.get_all_paged(
            skip=0,
            limit=20000, 
            aktif_only=False, # İptal sefeleri de görmek isteyebilirler
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
            arac_id=arac_id,
            sofor_id=sofor_id,
            durum=durum,
            search=search
        )
        
        # Pydantic -> Dict conversion
        data = []
        for s in seferler:
            d = s.model_dump()
            # Tarih/Saat formatlaması
            d["tarih"] = s.tarih.strftime("%Y-%m-%d") if s.tarih else ""
            d["durum"] = s.durum
            d["plaka"] = s.plaka or ""
            d["sofor"] = s.sofor_adi or ""
            # Gereksiz idleri temizle (Opsiyonel)
            data.append(d)
        
        content = ExcelService.export_data(data, type="sefer_listesi")
        
        filename = f"sefer_listesi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting trips: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Excel oluşturulurken hata oluştu")

from app.infrastructure.resilience.rate_limiter import RateLimiterDependency
from fastapi import Depends

@router.post("/", response_model=SeferResponse, dependencies=[Depends(RateLimiterDependency("create_trip", rate=2.0, period=1.0))])
async def create_sefer(
    sefer: SeferCreate, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Yeni sefer oluştur (Service Layer)."""
    service = get_sefer_service()
    try:
        sefer_id = await service.add_sefer(sefer)
        
        # Use service to get detailed object (avoids N+1 lazy loading issues)
        created = await service.get_sefer_by_id(sefer_id)
        return created
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")

@router.get("/{sefer_id}", response_model=SeferResponse)
async def read_sefer(
    sefer_id: int, 
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    sefer = await db.get(Sefer, sefer_id)
    if not sefer:
        raise HTTPException(status_code=404, detail="Sefer bulunamadı")
    return sefer

@router.put("/{sefer_id}", response_model=SeferResponse)
async def update_sefer(
    sefer_id: int, 
    sefer_in: SeferUpdate, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    service = get_sefer_service()
    try:
        # Existing Logic for Update (Safe):
        sefer = await db.get(Sefer, sefer_id)
        if not sefer: return None
        update_data = sefer_in.model_dump(exclude_unset=True)
        for k,v in update_data.items(): setattr(sefer, k, v)
        db.add(sefer)
        await db.commit()
        await db.refresh(sefer)
        logger.info(f"Trip updated: ID {sefer.id} by {current_admin.kullanici_adi}")
        return sefer

    except Exception as e:
        logger.error(f"Update error: {e}")
        raise HTTPException(status_code=500)

@router.delete("/{sefer_id}", response_model=dict)
async def delete_sefer(
    sefer_id: int, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Sefer sil (Hard Delete)."""
    service = get_sefer_service()
    
    try:
        success = await service.delete_sefer(sefer_id)
        if not success:
             raise HTTPException(status_code=404, detail="Sefer bulunamadı veya silinemedi")
             
        return {"status": "success", "message": "Sefer tamamen silindi"}

    except Exception as e:
        logger.error(f"Error deleting trip: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Silme hatası")

@router.post("/upload", response_model=dict)
async def upload_sefer_excel(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    file: UploadFile = File(...)
):
    from app.core.services.import_service import get_import_service
    
    # MIME Type Validation
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream"
    }
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.")
    
    # File extension validation
    if file.filename and not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Dosya uzantısı .xlsx veya .xls olmalıdır.")
    
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # 1. Check Content-Length header (fast fail)
    if file.size and file.size > MAX_FILE_SIZE:
         raise HTTPException(status_code=413, detail="Dosya boyutu 10MB'ı geçemez.")

    # 2. Secure Read (Chunked) protecting RAM
    content = bytearray()
    chunk_size = 1024 * 1024 # 1MB chunks
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE:
             raise HTTPException(status_code=413, detail="Dosya boyutu 10MB'ı geçemez.")
    
    import_service = get_import_service()
    
    # Convert bytearray back to bytes
    count, errors = await import_service.process_sefer_import(bytes(content))
    
    return {
        "status": "success" if not errors else "partial_success",
        "processed": count,
        "saved": count,
        "errors": errors
    }
