from app.infrastructure.events.event_bus import Event, EventType, get_event_bus
from app.infrastructure.logging.logger import get_logger
from app.core.services.anomaly_detector import (
    get_anomaly_detector,
    AnomalyResult,
    AnomalyType,
    SeverityEnum,
)

logger = get_logger(__name__)


async def handle_anomaly_detected(event: Event) -> None:
    """
    ANOMALY_DETECTED olayını yakala ve veritabanına kaydet.
    """
    data = event.data
    logger.info(
        f"Anomali Olayı İşleniyor: {data.get('tip')} - Arac {data.get('arac_id')}"
    )

    try:
        detector = get_anomaly_detector()

        # Event verisinden AnomalyResult oluştur
        anomaly = AnomalyResult(
            tip=AnomalyType(data.get("tip", "tuketim")),
            kaynak_tip="arac",
            kaynak_id=data.get("arac_id"),
            deger=data.get("deger", 0.0),
            beklenen_deger=data.get("beklenen_deger", 0.0),
            sapma_yuzde=data.get("sapma_yuzde", 0.0),
            severity=SeverityEnum(data.get("severity", "medium")),
            aciklama=data.get("aciklama", "Otomatik tespit edilen anomali"),
            tarih=data.get("tarih"),
        )

        # DB'ye kaydet
        await detector.save_anomalies([anomaly])

    except Exception as e:
        logger.error(f"Anomali işleme hatası: {e}", exc_info=True)


def register_anomaly_handlers():
    """Handler'ı EventBus'a kaydet"""
    bus = get_event_bus()
    bus.subscribe(EventType.ANOMALY_DETECTED, handle_anomaly_detected)
    logger.info("Anomaly handlers registered")
