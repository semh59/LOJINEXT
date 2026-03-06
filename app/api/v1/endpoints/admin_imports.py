from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from typing import Dict
from app.api.deps import get_current_user
from app.infrastructure.security.permission_checker import require_yetki
from app.database.models import Kullanici
from app.core.services.import_service import ImportService, get_import_service
from app.database.unit_of_work import UnitOfWork
from app.api.middleware.rate_limiter import limiter
from pydantic import BaseModel
import json

router = APIRouter()
# Removed global instantiation to support proper DI


class MappingData(BaseModel):
    mapping: Dict[str, str]


@router.post(
    "/preview",
    summary="İçeri Aktarım Önizleme",
    dependencies=[Depends(require_yetki("import_goruntule"))],
)
async def preview_import(
    file: UploadFile = File(...),
    aktarim_tipi: str = Form(...),
    current_user: Kullanici = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service),
):
    """Excel veya CSV dosyasının başlıklarını okur ve 5 satırlık önizleme sunar."""
    try:
        return await import_service.parse_and_preview(file, aktarim_tipi)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/commit",
    summary="İçeri Aktarım İşlemini Başlat",
    dependencies=[Depends(require_yetki(["import_rollback", "all", "*"]))],
)
async def commit_import(
    file: UploadFile = File(...),
    aktarim_tipi: str = Form(...),
    mapping_str: str = Form(...),  # JSON string
    current_user: Kullanici = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service),
):
    """
    Eşleştirilen alanlara göre veri tabanına bulk insert yapar.
    Oluşturulan track_id (islem_haritasi) geri alımı mümkün kılar.
    """
    try:
        mapping = json.loads(mapping_str)
        return await import_service.execute_import(
            file, aktarim_tipi, current_user.id, mapping
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Geçersiz mapping formatı.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Aktarım Hatası: {str(e)}")


@router.post(
    "/{job_id}/rollback",
    summary="Aktarım İşlemini Geri Al",
    dependencies=[Depends(require_yetki(["import_rollback", "all", "*"]))],
)
@limiter.limit("10/day")
async def rollback_import(
    job_id: int,
    request: Request,
    current_user: Kullanici = Depends(get_current_user),
    import_service: ImportService = Depends(get_import_service),
):
    """
    Geçmiş bir işlemi transaction içerisinde geri alır.
    """
    try:
        success = await import_service.rollback_import(job_id, current_user.id)
        return {"success": success, "message": "Geri alma işlemi başarıyla tamamlandı."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/history",
    summary="Geçmiş Aktarımlar",
    dependencies=[Depends(require_yetki("import_goruntule"))],
)
async def import_history(
    limit: int = 50, current_user: Kullanici = Depends(get_current_user)
):
    """
    Geçmişe dönük yükleme loglarını getirir.
    """
    async with UnitOfWork() as uow:
        jobs = await uow.import_repo.get_recent_jobs(limit=limit)
        return [
            {
                "id": job.id,
                "dosya_adi": job.dosya_adi,
                "aktarim_tipi": job.aktarim_tipi,
                "durum": job.durum,
                "toplam": job.toplam_kayit,
                "basarili": job.basarili_kayit,
                "hatali": job.hatali_kayit,
                "baslama_zamani": job.baslama_zamani,
                "yukleyen_id": job.yukleyen_id,
            }
            for job in jobs
        ]
