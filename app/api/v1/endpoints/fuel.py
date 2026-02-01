from typing import List, Annotated

from app.api.deps import SessionDep, get_current_user, get_current_active_admin
from app.database.models import YakitAlimi, Kullanici
from app.schemas.yakit import YakitCreate, YakitResponse, YakitUpdate
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy import select

from app.infrastructure.logging.logger import get_logger
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, Query, Response

from app.core.services.yakit_service import get_yakit_service

logger = get_logger(__name__)
router = APIRouter()

# read_yakit_alimlari wrapped in try/except

@router.get("/", response_model=List[YakitResponse])
async def read_yakit_alimlari(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = 100
):
    """Yakıt alımlarını listele (Service Layer)."""
    service = get_yakit_service()
    try:
        # Service handles skip/limit/safety/validation internally
        return await service.get_all_paged(skip=skip, limit=limit)
    except Exception as e:
         logger.error(f"Error listing fuel via service: {e}")
         raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")

from app.infrastructure.resilience.rate_limiter import RateLimiterDependency
from fastapi import Depends

@router.post("/", response_model=YakitResponse, dependencies=[Depends(RateLimiterDependency("create_fuel", rate=2.0, period=1.0))])
async def create_yakit(
    yakit: YakitCreate, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    service = get_yakit_service()
    try:
        # Create via Service (Audit Log + Outlier Check)
        yakit_id = await service.add_yakit(yakit)
        created = await db.get(YakitAlimi, yakit_id)
        return created
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating fuel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")

@router.get("/{yakit_id}", response_model=YakitResponse)
async def read_yakit(
    yakit_id: int, 
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    yakit = await db.get(YakitAlimi, yakit_id)
    if not yakit:
        raise HTTPException(status_code=404, detail="Yakıt alımı bulunamadı")
    return yakit

@router.put("/{yakit_id}", response_model=YakitResponse)
async def update_yakit(
    yakit_id: int, 
    yakit_in: YakitUpdate, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    # Hybrid update for now (Safe)
    yakit = await db.get(YakitAlimi, yakit_id)
    if not yakit:
        raise HTTPException(status_code=404, detail="Yakıt alımı bulunamadı")

    update_data = yakit_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(yakit, field, value)

    db.add(yakit)
    await db.commit()
    await db.refresh(yakit)
    logger.info(f"Fuel record updated: ID {yakit.id} by {current_admin.kullanici_adi}")
    return yakit

@router.delete("/{yakit_id}", response_model=YakitResponse)
async def delete_yakit(
    yakit_id: int, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    response: Response
):
    """Yakıt alımı sil (Service: Smart Delete)."""
    service = get_yakit_service()
    
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

@router.post("/upload", response_model=dict)
async def upload_yakit_excel(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    file: UploadFile = File(...)
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
    
    count, errors = await import_service.process_yakit_import(bytes(content))
    
    return {
        "status": "success" if not errors else "partial_success",
        "processed": count,
        "saved": count,
        "errors": errors
    }

