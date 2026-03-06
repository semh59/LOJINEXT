import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.services.notification_service import NotificationService
from app.infrastructure.events.event_bus import Event, EventType


@pytest.mark.asyncio
async def test_notification_service_handles_sefer_updated():
    """Verify that SEFER_UPDATED event triggers notification creation."""
    service = NotificationService()

    with patch("app.core.services.notification_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_uow.commit = AsyncMock()

        # Mock Rule
        mock_rule = MagicMock(
            olay_tipi=EventType.SEFER_UPDATED, kanallar=["UI"], alici_rol_id=2
        )
        mock_uow.notification_repo.get_rules_by_event = AsyncMock(
            return_value=[mock_rule]
        )

        # Mock Target Users
        mock_uow.kullanici_repo.get_by_rol_id = AsyncMock(
            return_value=[MagicMock(id=10, email="test@test.com")]
        )

        mock_uow.notification_repo.add = AsyncMock()

        event = Event(
            type=EventType.SEFER_UPDATED,
            data={"sefer_id": 123, "trigger": "test_override"},
        )
        await service.handle_event(event)

        # Verify notification was added
        mock_uow.notification_repo.add.assert_called()
        mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mark_notification_as_read():
    """Verify status update to READ."""
    service = NotificationService()

    with patch("app.core.services.notification_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_uow.commit = AsyncMock()
        mock_uow.notification_repo.update = AsyncMock(return_value=True)

        success = await service.mark_as_read(1)
        assert success is True
        mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_notifications():
    """Verify retrieval of notifications for a specific user."""
    service = NotificationService()

    with patch("app.core.services.notification_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_notification = MagicMock(id=1, kullanici_id=10, baslik="Test")
        mock_uow.notification_repo.get_user_notifications = AsyncMock(
            return_value=[mock_notification]
        )

        notifications = await service.get_user_notifications(10)
        assert len(notifications) == 1
        assert notifications[0].id == 1
        mock_uow.notification_repo.get_user_notifications.assert_called_with(10)


@pytest.mark.asyncio
async def test_handle_event_no_rules():
    """Verify that event handling exits gracefully when no rules match."""
    service = NotificationService()

    with patch("app.core.services.notification_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_uow.notification_repo.get_rules_by_event = AsyncMock(return_value=[])

        event = Event(type="UNMAPPED_EVENT", data={})
        await service.handle_event(event)

        # Should not fetch users or add notifications
        mock_uow.kullanici_repo.get_by_rol_id.assert_not_called()
        mock_uow.notification_repo.add.assert_not_called()
