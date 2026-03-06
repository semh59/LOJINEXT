from typing import List
from datetime import datetime
from app.database.unit_of_work import UnitOfWork
from app.database.models import BildirimDurumu, BildirimGecmisi
from app.infrastructure.events.event_bus import get_event_bus, Event, EventType
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for processing system events and delivering notifications."""

    def __init__(self):
        self.event_bus = get_event_bus()

    def register_handlers(self):
        """Register the service to listen for all critical events."""
        self.event_bus.subscribe(EventType.SEFER_UPDATED, self.handle_event)
        self.event_bus.subscribe(EventType.SLA_DELAY, self.handle_event)
        # Add more event types as needed
        logger.info("NotificationService handlers registered.")

    async def handle_event(self, event: Event):
        """Process an incoming event and create notifications based on rules."""
        async with UnitOfWork() as uow:
            rules = await uow.notification_repo.get_rules_by_event(event.type)
            if not rules:
                return

            for rule in rules:
                # 1. Fetch target users by role
                users = await uow.kullanici_repo.get_by_rol_id(rule.alici_rol_id)

                for user in users:
                    # 2. Create Notification Record
                    header, content = self._format_message(event)

                    for channel in rule.kanallar:
                        notification = BildirimGecmisi(
                            kullanici_id=user.id,
                            baslik=header,
                            icerik=content,
                            olay_tipi=event.type.value,
                            kanal=channel,
                            durum=BildirimDurumu.SENT,
                        )
                        await uow.notification_repo.add(notification)

                        # 3. Channel Specific Delivery Trigger
                        if channel == "UI":
                            from app.api.v1.endpoints.admin_ws import (
                                notification_ws_manager,
                            )

                            # Push to WebSocket if user is online
                            # We use user.email as the identifier in WS manager
                            await notification_ws_manager.send_personal_message(
                                {
                                    "type": "notification",
                                    "data": {
                                        "id": notification.id,
                                        "baslik": header,
                                        "icerik": content,
                                        "olay_tipi": event.type.value,
                                        "olusturma_tarihi": datetime.now().isoformat(),
                                    },
                                },
                                user.email,
                            )
                            logger.info(f"UI Notification pushed to user {user.id}")
                        elif channel == "EMAIL":
                            logger.info(f"Email task queued for user {user.email}")

            await uow.commit()

    def _format_message(self, event: Event) -> tuple:
        """Construct human-readable header and content from event data."""
        if event.type == EventType.SEFER_UPDATED:
            sefer_id = event.data.get("sefer_id")
            trigger = event.data.get("trigger")
            header = f"Sefer Güncellendi: #{sefer_id}"
            content = f"Sefer verileri '{trigger}' nedeniyle güncellendi. Yakıt ve performans değerleri yeniden hesaplandı."
            return header, content

        if event.type == EventType.SLA_DELAY:
            sefer_id = event.data.get("sefer_id")
            delay_min = event.data.get("delay_min", 0)
            header = "📦 Lojistik Gecikme (SLA İhlali)"
            content = f"#{sefer_id} nolu seferde {delay_min} dakikalık gecikme tespit edildi. Teslimat hedefi aşıldı."
            return header, content

        if event.type == EventType.ANOMALY_DETECTED:
            header = "⚠️ Anomali Tespit Ediidi"
            content = event.data.get(
                "aciklama", "Sistemde sıra dışı bir veri tespit edildi."
            )
            return header, content

        return "Sistem Mesajı", str(event.data)

    async def get_user_notifications(self, user_id: int) -> List[BildirimGecmisi]:
        """Fetch unread or recent notifications for the logged-in user."""
        async with UnitOfWork() as uow:
            return await uow.notification_repo.get_user_notifications(user_id)

    async def mark_as_read(self, notification_id: int) -> bool:
        """Update notification status to READ."""
        async with UnitOfWork() as uow:
            success = await uow.notification_repo.update(
                notification_id, durum=BildirimDurumu.READ, okundu_tarihi=datetime.now()
            )
            if success:
                await uow.commit()
            return success

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications of a user as read."""
        async with UnitOfWork() as uow:
            count = await uow.notification_repo.mark_all_as_read(user_id)
            if count > 0:
                await uow.commit()
            return count
