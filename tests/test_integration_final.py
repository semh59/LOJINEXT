import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.services.notification_service import NotificationService
from app.infrastructure.events.event_bus import Event, EventType


@pytest.mark.asyncio
async def test_end_to_end_flow_sefer_update_to_notification():
    """
    E2E Scenario: A trip is updated (mocking service call),
    which triggers an EventBus event,
    which is then handled by NotificationService to create a record.
    """
    notif_service = NotificationService()

    with patch("app.core.services.notification_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        # 1. Setup Notification Rules
        mock_rule = MagicMock(
            olay_tipi=EventType.SEFER_UPDATED, kanallar=["UI"], alici_rol_id=2
        )
        mock_uow.notification_repo.get_rules_by_event = AsyncMock(
            return_value=[mock_rule]
        )
        mock_uow.notification_repo.add = AsyncMock()

        # 2. Setup Target Users (e.g. Fleet Managers)
        mock_user = MagicMock(id=50, email="fleet@lojinext.com")
        mock_uow.kullanici_repo.get_by_rol_id = AsyncMock(return_value=[mock_user])

        # 3. Simulate Event from SeferService
        event = Event(
            type=EventType.SEFER_UPDATED,
            data={"sefer_id": 999, "status": "COMPLETED", "trigger": "test_e2e"},
        )

        # 4. Handle Event
        await notif_service.handle_event(event)

        # 5. Assertions
        # Notification should be added to repo
        mock_uow.notification_repo.add.assert_called()
        # Transaction should be committed
        mock_uow.commit.assert_called_once()

        # Verify content check (optional refinement)
        args, kwargs = mock_uow.notification_repo.add.call_args
        notification_obj = args[0]
        assert "999" in notification_obj.mesaj  # Mesaj contains sefer_id
        assert notification_obj.kullanici_id == 50
