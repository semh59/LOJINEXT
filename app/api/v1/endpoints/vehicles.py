from typing import List, Annotated, Optional
from datetime import datetime

from app.api.deps import SessionDep, get_current_user, get_current_active_admin
from app.database.models import Arac, Kullanici
from app.schemas.arac import AracCreate, AracResponse, AracUpdate
from app.core.services.excel_service import ExcelService
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query, Response
from sqlalchemy import select, or_

from app.infrastructure.logging.logger import get_logger
from app.core.services.arac_service import get_arac_service

logger = get_logger(__name__)
router = APIRouter()

# ... read_araclar (Keep as is, but maybe use service.get_all later?) ...
# For now, let's keep read_araclar direct for performance unless service wraps it.
# Service does wrap it: get_all_vehicles. But read_araclar has complex filtering.
# Let's clean up Create/Update/Delete first.

@router.get("/", response_model=List[AracResponse])
async def read_araclar(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    aktif_only: bool = True,
    search: str = Query(None, min_length=1),
    marka: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    min_yil: Optional[int] = Query(None),
    max_yil: Optional[int] = Query(None)
):
    """Araçları listele (Service Layer)."""
    service = get_arac_service()
    try:
        # Centralized listing with safety and filtering
        return await service.get_all_paged(
            skip=skip,
            limit=limit,
            aktif_only=aktif_only,
            search=search,
            marka=marka,
            model=model,
            min_yil=min_yil,
            max_yil=max_yil
        )
    except Exception as e:
        logger.error(f"Error listing vehicles via service: {e}")
        raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")
    except Exception as glob_e:
        logger.error(f"CRITICAL API ERROR in read_araclar: {glob_e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {glob_e}")

@router.get("/export")
async def export_araclar(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    aktif_only: bool = True,
    search: str = Query(None, min_length=1),
    marka: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    min_yil: Optional[int] = Query(None),
    max_yil: Optional[int] = Query(None)
):
    """Araç listesini Excel olarak dışa aktar (Filtreli)."""
    service = get_arac_service()
    try:
        # Export için limit kaldırılır (veya çok yüksek tutulur)
        vehicles = await service.get_all_paged(
            skip=0,
            limit=10000, # Makul bir üst sınır
            aktif_only=aktif_only,
            search=search,
            marka=marka,
            model=model,
            min_yil=min_yil,
            max_yil=max_yil
        )
        
        # Pydantic modellerini dict'e çevir
        data = [v.model_dump() for v in vehicles]
        
        # Excel oluştur
        content = ExcelService.export_data(data, type="arac_listesi")
        
        filename = f"arac_listesi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting vehicles: {e}")
        raise HTTPException(status_code=500, detail="Excel oluşturulurken hata oluştu")

@router.post("/", response_model=AracResponse)
async def create_arac(
    arac: AracCreate, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Yeni araç oluştur (Service: Duplicate Check + Reactivation)."""
    service = get_arac_service()
    try:
        arac_id = await service.create_arac(arac)
        
        # Fetch created
        created = await db.get(Arac, arac_id)
        if not created:
             raise HTTPException(status_code=500, detail="Araç oluşturuldu ancak okunamadı.")
             
        logger.info(f"Vehicle processed via Service: {created.plaka} by {current_admin.kullanici_adi}")
        return created
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vehicle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")

@router.get("/template")
async def get_vehicle_template(
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """Araç yükleme Excel şablonunu indir."""
    from fastapi.responses import Response
    from app.core.services.excel_service import ExcelService
    
    content = ExcelService.generate_template("arac")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=arac_yukleme_sablonu.xlsx"
        }
    )

@router.delete("/clear-all")
async def clear_all_vehicles(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Tüm araçları temizle (Admin Only)."""
    service = get_arac_service()
    try:
        count = await service.delete_all_vehicles()
        return {"status": "success", "message": f"{count} araç temizlendi."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error clearing all vehicles: {e}")
        raise HTTPException(status_code=500, detail="Temizleme işlemi sırasında hata oluştu")

@router.delete("/{arac_id}")
async def delete_arac(
    arac_id: int,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Araç sil (Soft/Hard delete)."""
    service = get_arac_service()
    try:
        success = await service.delete_arac(arac_id)
        if not success:
             raise HTTPException(status_code=404, detail="Araç bulunamadı")
        return {"status": "success", "message": "Araç silindi"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting vehicle {arac_id}: {e}")
        raise HTTPException(status_code=500, detail="Silme işlemi başarısız")

@router.get("/{arac_id}", response_model=AracResponse)
async def read_arac(
    arac_id: int, 
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """Araç detayını getir."""
    arac = await db.get(Arac, arac_id)
    if not arac:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")
    return arac

@router.put("/{arac_id}", response_model=AracResponse)
async def update_arac(
    arac_id: int,
    arac_update: AracUpdate,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """Araç güncelle."""
    from sqlalchemy import select
    
    # Mevcut aracı bul
    result = await db.execute(select(Arac).where(Arac.id == arac_id))
    existing = result.scalar_one_or_none()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Araç bulunamadı")
    
    # Güncelleme verilerini uygula
    update_data = arac_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing, field, value)
    
    await db.commit()
    await db.refresh(existing)
    
    logger.info(f"Vehicle updated: {existing.plaka} by {current_admin.kullanici_adi}")
    return existing

@router.post("/upload")
async def upload_vehicles(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    file: UploadFile = File(...)
):
    # ... existing implementation ...
    from app.core.services.import_service import get_import_service
    
    # MIME Type Validation
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "application/vnd.ms-excel",  # xls
        "application/octet-stream"  # Some browsers send this
    }
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Sadece Excel dosyaları (.xlsx, .xls) kabul edilir.")
    
    # File extension validation (double check)
    if file.filename:
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Dosya uzantısı .xlsx veya .xls olmalıdır.")
    
    # 10MB Limit Check
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
    
    created_count, errors = await import_service.process_vehicle_import(bytes(content))
    
    return {
        "status": "success",
        "message": f"{created_count} araç yüklendi.",
        "errors": errors
    }



