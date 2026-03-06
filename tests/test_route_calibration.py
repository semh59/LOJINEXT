import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from app.core.services.route_calibration_service import RouteCalibrationService
from app.database.unit_of_work import UnitOfWork


@pytest.mark.asyncio
async def test_calibrate_route_from_trip_logic():
    """Verify route calibration."""
    mock_db = AsyncMock()
    uow = UnitOfWork(mock_db)

    with (
        patch("app.database.unit_of_work.UnitOfWork.commit", new_callable=AsyncMock),
        patch(
            "app.database.unit_of_work.UnitOfWork.sefer_repo", new_callable=PropertyMock
        ) as mock_sefer_prop,
        patch(
            "app.database.unit_of_work.UnitOfWork.lokasyon_repo",
            new_callable=PropertyMock,
        ) as mock_lok_prop,
    ):
        mock_sefer_repo = MagicMock()
        mock_sefer_repo.get = AsyncMock(
            return_value=MagicMock(
                id=1,
                guzergah_id=10,
                rota_detay={"coordinates": [[29.0, 41.0], [29.1, 41.1]]},
            )
        )
        mock_sefer_prop.return_value = mock_sefer_repo

        mock_lok_repo = MagicMock()
        mock_lok_repo.get = AsyncMock()
        mock_lok_prop.return_value = mock_lok_repo

        uow.session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=lambda: None)
        )
        uow.session.add = MagicMock()  # session.add is usually sync in SQLAlchemy

        service = RouteCalibrationService(uow)
        success = await service.calibrate_route_from_trip(1)
        assert success is True


@pytest.mark.asyncio
async def test_match_sefer_to_path_logic():
    """Verify spatial matching return."""
    mock_db = AsyncMock()
    uow = UnitOfWork(mock_db)

    with patch(
        "app.database.unit_of_work.UnitOfWork.sefer_repo", new_callable=PropertyMock
    ) as mock_sefer_prop:
        mock_sefer_repo = MagicMock()
        mock_sefer_repo.get = AsyncMock(
            return_value=MagicMock(
                id=1,
                guzergah_id=10,
                rota_detay={"coordinates": [[29.0, 41.0], [29.1, 41.1]]},
            )
        )
        mock_sefer_prop.return_value = mock_sefer_repo

        uow.session.execute = AsyncMock(
            return_value=MagicMock(
                scalar_one_or_none=lambda: MagicMock(hedef_path="WKB")
            )
        )

        service = RouteCalibrationService(uow)
        result = await service.match_sefer_to_path(1)
        assert result["status"] == "calculated"
        assert result["matches"] is True
