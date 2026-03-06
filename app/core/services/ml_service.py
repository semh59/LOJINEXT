from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from datetime import datetime, timezone

from app.database.unit_of_work import UnitOfWork
from app.database.models import EgitimKuyrugu, ModelVersiyon
from app.infrastructure.logging.logger import get_logger
from app.api.v1.endpoints.admin_ws import training_ws_manager

logger = get_logger(__name__)


class MLService:
    """
    Elite Service for ML Model Versioning & Training Queue Logic.
    Operates strictly via Unit of Work (UoW).
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def schedule_training(
        self, arac_id: int, user_id: Optional[int] = None
    ) -> EgitimKuyrugu:
        """Schedule a new model training task."""
        async with self.uow:
            # Check if there's already an active task logic
            active_tasks = await self.uow.ml_training_repo.get_active_tasks_for_vehicle(
                arac_id
            )
            if active_tasks:
                raise HTTPException(
                    status_code=400,
                    detail="Araç için zaten aktif bir eğitim görevi bulunuyor.",
                )

            # Calculate next target version
            latest_version = await self.uow.model_versiyon_repo.get_latest_version(
                arac_id
            )
            next_version = 1 if latest_version is None else latest_version + 1

            new_task = EgitimKuyrugu(
                arac_id=arac_id,
                hedef_versiyon=next_version,
                durum="WAITING",
                tetikleyen_kullanici_id=user_id,
            )
            self.uow.session.add(new_task)
            await self.uow.commit()

            logger.info(
                f"Scheduled new training task for vehicle {arac_id} (Version {next_version})"
            )
            return new_task

    async def get_training_queue(self, limit: int = 50) -> List[EgitimKuyrugu]:
        """Get current training queue."""
        async with self.uow:
            return await self.uow.ml_training_repo.get_pending_tasks(limit)

    async def update_task_progress(
        self,
        task_id: int,
        ilerleme: float,
        durum: str,
        is_error: bool = False,
        hata_detay: Optional[str] = None,
    ):
        """Update progress / status of a training task."""
        async with self.uow:
            task = await self.uow.ml_training_repo.get_by_id(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Eğitim görevi bulunamadı")

            task.ilerleme = ilerleme
            task.durum = durum

            if is_error:
                task.hata_detay = hata_detay

            if durum in ["RUNNING", "COMPLETED", "FAILED"]:
                task.guncelleme = datetime.now(timezone.utc)
                if durum == "RUNNING" and not task.baslangic_zaman:
                    task.baslangic_zaman = datetime.now(timezone.utc)
                if durum in ["COMPLETED", "FAILED"]:
                    task.bitis_zaman = datetime.now(timezone.utc)

            await self.uow.commit()

            # Propagate via WebSocket to Admin Panel UI
            await training_ws_manager.broadcast(
                {
                    "type": "progress",
                    "task_id": task_id,
                    "arac_id": task.arac_id,
                    "ilerleme": ilerleme,
                    "durum": durum,
                    "is_error": is_error,
                    "hata_detay": hata_detay,
                }
            )

    async def register_model_version(
        self,
        arac_id: int,
        versiyon: int,
        metrics: Dict[str, Any],
        model_dosya_yolu: str,
        kullanilan_ozellikler: dict,
        veri_sayisi: int,
    ) -> ModelVersiyon:
        """Register a newly trained model version."""
        async with self.uow:
            new_version = ModelVersiyon(
                arac_id=arac_id,
                versiyon=versiyon,
                veri_sayisi=veri_sayisi,
                r2_skoru=metrics.get("r2_skoru"),
                mae=metrics.get("mae"),
                mape=metrics.get("mape"),
                rmse=metrics.get("rmse"),
                model_dosya_yolu=model_dosya_yolu,
                kullanilan_ozellikler=kullanilan_ozellikler,
                xgboost_agirligi=metrics.get("xgboost_agirligi"),
                lightgbm_agirligi=metrics.get("lightgbm_agirligi"),
                rf_agirligi=metrics.get("rf_agirligi"),
            )
            self.uow.session.add(new_version)
            await self.uow.commit()

            logger.info(
                f"Registered new model version {versiyon} for vehicle {arac_id}"
            )
            return new_version
