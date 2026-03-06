"""
Model Training Handler
Listens to domain events and triggers background operations.
"""

import asyncio
from typing import Dict

from app.infrastructure.events.event_bus import get_event_bus, EventType, Event
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ModelTrainingHandler:
    """
    EventBus üzerinden gelen YAKIT_ADDED ve SEFER_ADDED event'larını dinleyip,
    belirli bir limite ulaştığında ilgili aracın ML modelini otomatik eğiten sınıf.
    """

    def __init__(self):
        self.event_bus = get_event_bus()
        self.trigger_counts: Dict[int, int] = {}
        self.TRIGGER_THRESHOLD = 5  # Her 5 yeni yakıt/sefer kaydında retrain tetikle
        self._is_subscribed = False

    def setup(self):
        """Abonelikleri başlat."""
        if self._is_subscribed:
            return

        self.event_bus.subscribe(EventType.YAKIT_ADDED, self.on_data_added)
        self.event_bus.subscribe(EventType.SEFER_ADDED, self.on_data_added)
        self._is_subscribed = True
        logger.info("ModelTrainingHandler subscribed to YAKIT_ADDED and SEFER_ADDED")

    async def on_data_added(self, event: Event):
        """Yeni veri geldiğinde counter update."""
        vehicle_id = event.data.get("arac_id")

        if not vehicle_id:
            logger.debug(
                f"ModelTrainingHandler: Event {event.type.value} does not have arac_id"
            )
            return

        # Sayaç artırımı
        self.trigger_counts[vehicle_id] = self.trigger_counts.get(vehicle_id, 0) + 1
        current_count = self.trigger_counts[vehicle_id]

        logger.debug(
            f"ModelTrainingHandler | arac_id: {vehicle_id} | event: {event.type.value} | "
            f"count: {current_count}/{self.TRIGGER_THRESHOLD}"
        )

        # Threshold aşıldıysa eğitimi tetikle
        if current_count >= self.TRIGGER_THRESHOLD:
            self.trigger_counts[vehicle_id] = 0  # Reset
            logger.info(
                f"ModelTrainingHandler: Auto-training triggered for vehicle_id: {vehicle_id}"
            )

            try:
                # Circular dependency'i engellemek için fonksiyon içinde import alıyoruz
                from app.core.ml.ensemble_predictor import (
                    get_ensemble_service,
                )

                svc = get_ensemble_service()

                # Asenkron bir eğitimi arka planda başlat (task olarak)
                loop = asyncio.get_running_loop()
                if loop and loop.is_running():
                    loop.create_task(svc.train_for_vehicle(vehicle_id))

                    # Ayrıca RAG'i güncellemek için bir EVENT tetikleyebiliriz
                    from app.infrastructure.events.event_bus import EventType

                    self.event_bus.publish_simple(
                        EventType.CACHE_INVALIDATED, entity="model", arac_id=vehicle_id
                    )

            except Exception as e:
                logger.error(
                    f"Error triggering auto-train for vehicle {vehicle_id}: {e}"
                )


# Singleton Instance
_model_training_handler = None


def get_model_training_handler() -> ModelTrainingHandler:
    global _model_training_handler
    if _model_training_handler is None:
        _model_training_handler = ModelTrainingHandler()
    return _model_training_handler
