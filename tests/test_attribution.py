import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from app.core.services.attribution_service import AttributionService
from app.infrastructure.events.event_bus import Event, EventType


@pytest.mark.asyncio
async def test_attribution_override_publishes_event():
    """Verify attribution override publishes event."""
    from app.database.unit_of_work import UnitOfWork

    uow = UnitOfWork(AsyncMock())

    with (
        patch("app.database.unit_of_work.UnitOfWork.commit", new_callable=AsyncMock),
        patch(
            "app.database.unit_of_work.UnitOfWork.sefer_repo", new_callable=PropertyMock
        ) as mock_sefer_prop,
        patch(
            "app.database.unit_of_work.UnitOfWork.audit_repo", new_callable=PropertyMock
        ) as mock_audit_prop,
    ):
        mock_sefer_repo = MagicMock()
        mock_sefer_repo.get = AsyncMock()
        mock_sefer_repo.update = AsyncMock()
        mock_sefer_prop.return_value = mock_sefer_repo

        mock_audit_repo = MagicMock()
        mock_audit_repo.add = AsyncMock()
        mock_audit_prop.return_value = mock_audit_repo

        mock_sefer = MagicMock()
        mock_sefer.id = 123
        mock_sefer.arac_id = 1
        mock_sefer_repo.get.return_value = mock_sefer

        with patch(
            "app.core.services.attribution_service.get_event_bus"
        ) as mock_get_eb:
            mock_eb = MagicMock()
            mock_eb.publish_async = AsyncMock()
            mock_get_eb.return_value = mock_eb

            service = AttributionService(uow)
            await service.override_attribution(123, 2, 2, "Reason")

            mock_eb.publish_async.assert_called_once()


@pytest.mark.asyncio
async def test_physics_handler_execution():
    """Verify physics handler recalculation."""
    from app.core.handlers.physics_handler import PhysicsRecalculationHandler

    with patch("app.database.db_session.get_async_session_context") as mock_ctx:
        mock_db = AsyncMock()
        mock_ctx.return_value.__aenter__.return_value = mock_db

        with patch("app.core.handlers.physics_handler.UnitOfWork") as mock_uow_cls:
            mock_uow = MagicMock()
            mock_uow.__aenter__.return_value = mock_uow
            mock_uow_cls.return_value = mock_uow

            mock_uow.commit = AsyncMock()
            mock_uow.sefer_repo.get = AsyncMock(
                return_value=MagicMock(
                    id=123,
                    arac_id=1,
                    mesafe_km=100.0,
                    ton=20.0,
                    bos_sefer=False,
                    ascent_m=0.0,
                    descent_m=0.0,
                    flat_distance_km=100.0,
                )
            )
            mock_uow.arac_repo.get = AsyncMock(
                return_value=MagicMock(
                    bos_agirlik_kg=8000.0,
                    hava_direnc_katsayisi=0.7,
                    on_kesit_alani_m2=8.5,
                    lastik_direnc_katsayisi=0.007,
                    motor_verimliligi=0.38,
                )
            )
            mock_uow.sefer_repo.update = AsyncMock()

            handler = PhysicsRecalculationHandler()
            event = Event(
                type=EventType.SEFER_UPDATED, data={"sefer_id": 123, "trigger": "test"}
            )
            await handler.on_sefer_updated(event)

            mock_uow.sefer_repo.update.assert_called_once()
