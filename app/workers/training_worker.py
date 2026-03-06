import asyncio
import traceback
import random

from app.database.unit_of_work import UnitOfWork
from app.core.services.ml_service import MLService
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def simulate_training_for_task(task_id: int):
    """
    Simulates ML training for a specific task.
    In a real scenario, this would call actual XGBoost/LightGBM pipelines.
    """
    uow = UnitOfWork()
    ml_service = MLService(uow)

    try:
        logger.info(f"[ML Worker] Starting training for task_id: {task_id}")
        await ml_service.update_task_progress(task_id, ilerleme=10.0, durum="RUNNING")

        # Simulate data extraction
        await asyncio.sleep(2)
        await ml_service.update_task_progress(task_id, ilerleme=30.0, durum="RUNNING")

        # Simulate model training
        await asyncio.sleep(3)
        await ml_service.update_task_progress(task_id, ilerleme=75.0, durum="RUNNING")

        # Simulate evaluation
        await asyncio.sleep(2)
        await ml_service.update_task_progress(task_id, ilerleme=95.0, durum="RUNNING")

        # Finalize and register version
        metrics = {
            "r2_skoru": 0.89 + random.uniform(-0.05, 0.05),
            "mae": 1.2 + random.uniform(-0.2, 0.2),
            "mape": 4.5 + random.uniform(-1.0, 1.0),
            "rmse": 1.8 + random.uniform(-0.3, 0.3),
            "xgboost_agirligi": 0.4,
            "lightgbm_agirligi": 0.4,
            "rf_agirligi": 0.2,
        }

        async with UnitOfWork() as session_uow:
            task = await session_uow.ml_training_repo.get_by_id(task_id)
            if task:
                arac_id = task.arac_id
                versiyon = task.hedef_versiyon
            else:
                raise ValueError(
                    f"Task ID {task_id} not found during completion phase."
                )

        await ml_service.register_model_version(
            arac_id=arac_id,
            versiyon=versiyon,
            metrics=metrics,
            model_dosya_yolu=f"s3://models/vehicle_{arac_id}/v{versiyon}.pkl",
            kullanilan_ozellikler={
                "features": ["distance", "speed", "load", "elevation"]
            },
            veri_sayisi=15000,
        )

        await ml_service.update_task_progress(
            task_id, ilerleme=100.0, durum="COMPLETED"
        )
        logger.info(f"[ML Worker] Successfully completed training task_id: {task_id}")

    except Exception as e:
        logger.error(f"[ML Worker] Error in task {task_id}: {e}", exc_info=True)
        # Attempt to mark as failed
        error_uow = UnitOfWork()
        error_ml = MLService(error_uow)
        await error_ml.update_task_progress(
            task_id,
            ilerleme=0.0,
            durum="FAILED",
            is_error=True,
            hata_detay=traceback.format_exc(),
        )


async def run_worker_loop():
    """Continuously poll for WAITING tasks and process them."""
    logger.info("[ML Worker] Starting ML Training Worker Loop...")
    while True:
        try:
            uow = UnitOfWork()
            ml_service = MLService(uow)
            tasks = await ml_service.get_training_queue(limit=5)

            for task in tasks:
                # Dispatch simulating task async so we don't block the loop completely
                asyncio.create_task(simulate_training_for_task(task.id))

        except Exception as e:
            logger.error(f"[ML Worker] Exception in worker loop: {e}", exc_info=True)

        await asyncio.sleep(10)  # Poll every 10 seconds


if __name__ == "__main__":
    asyncio.run(run_worker_loop())
