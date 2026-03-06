from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import select

from app.api.deps import (
    SessionDep,
    UOWDep,
    get_dorse_service,
    get_current_active_admin,
    get_current_user,
)
from app.core.services.dorse_service import DorseService
from app.database.models import Dorse, Kullanici
from app.infrastructure.logging.logger import get_logger
from app.schemas.dorse import DorseCreate, DorseResponse, DorseUpdate
from app.schemas.base import StandardResponse, ResponseMeta

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=StandardResponse[List[DorseResponse]])
async def read_dorseler(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    service: DorseService = Depends(get_dorse_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    aktif_only: bool = True,
    search: str = Query(None, min_length=1),
):
    """Dorseleri listele."""
    try:
        data = await service.get_all_paged(
            skip=skip,
            limit=limit,
            aktif_only=aktif_only,
            search=search,
        )
        return StandardResponse(
            data=data, meta=ResponseMeta(count=len(data), offset=skip, limit=limit)
        )
    except Exception as e:
        logger.error(f"Error listing trailers: {e}")
        raise HTTPException(status_code=500, detail="Liste alınırken hata oluştu")


@router.post("/", response_model=StandardResponse[DorseResponse], status_code=201)
async def create_dorse(
    dorse: DorseCreate,
    uow: UOWDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: DorseService = Depends(get_dorse_service),
):
    """Yeni dorse oluştur."""
    try:
        dorse_id = await service.create(**dorse.model_dump())
        created = await uow.dorse_repo.get_by_id(dorse_id)
        if not created:
            raise HTTPException(
                status_code=500, detail="Dorse oluşturuldu ancak okunamadı."
            )
        return StandardResponse(data=created)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating trailer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Sunucu hatası")


@router.get("/export")
async def export_trailers(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: DorseService = Depends(get_dorse_service),
):
    """Tüm dorseleri Excel olarak indir."""
    from fastapi.responses import Response

    content = await service.export_all_trailers()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dorseler.xlsx"},
    )


@router.get("/template")
async def get_trailer_template(
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: DorseService = Depends(get_dorse_service),
):
    """Dorse yükleme şablonunu indir."""
    from fastapi.responses import Response

    content = await service.get_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dorse_sablonu.xlsx"},
    )


@router.post("/import")
async def import_trailers(
    file: UploadFile,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: DorseService = Depends(get_dorse_service),
):
    """Excel'den dorse verileri yükle."""
    try:
        content = await file.read()
        result = await service.import_trailers(content)
        return StandardResponse(data=result)
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{dorse_id}", response_model=StandardResponse[DorseResponse])
async def read_dorse(
    dorse_id: int,
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """Dorse detayını getir."""
    dorse = await db.get(Dorse, dorse_id)
    if not dorse:
        raise HTTPException(status_code=404, detail="Dorse bulunamadı")
    return StandardResponse(data=dorse)


@router.put("/{dorse_id}", response_model=StandardResponse[DorseResponse])
async def update_dorse(
    dorse_id: int,
    dorse_update: DorseUpdate,
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: DorseService = Depends(get_dorse_service),
):
    """Dorse güncelle."""
    try:
        success = await service.update(
            dorse_id, **dorse_update.model_dump(exclude_unset=True)
        )
        if not success:
            raise HTTPException(status_code=404, detail="Dorse bulunamadı")

        result = await db.execute(select(Dorse).where(Dorse.id == dorse_id))
        updated = result.scalar_one_or_none()
        return StandardResponse(data=updated)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.delete("/{dorse_id}", response_model=StandardResponse[dict])
async def delete_dorse(
    dorse_id: int,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    service: DorseService = Depends(get_dorse_service),
):
    """Dorse sil."""
    try:
        success = await service.delete(dorse_id)
        if not success:
            raise HTTPException(status_code=404, detail="Dorse bulunamadı")
        return StandardResponse(data={"status": "success", "message": "Dorse silindi"})
    except Exception as e:
        logger.error(f"Error deleting trailer {dorse_id}: {e}")
        raise HTTPException(status_code=500, detail="Silme işlemi başarısız")
