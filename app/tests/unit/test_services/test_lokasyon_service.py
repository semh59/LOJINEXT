from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.services.lokasyon_service import LokasyonService
from app.schemas.lokasyon import LokasyonCreate, LokasyonUpdate


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    mock_bus = MagicMock()
    mock_bus.publish = AsyncMock()
    return LokasyonService(repo=mock_repo, event_bus=mock_bus)


@pytest.mark.asyncio
class TestLokasyonService:
    async def test_get_all_paged(self, service, mock_repo):
        # Mock get_all and count separately as service calls them individually
        mock_repo.get_all.return_value = [
            {"id": 1, "cikis_yeri": "A", "varis_yeri": "B", "mesafe_km": 100.0}
        ]
        mock_repo.count.return_value = 1

        result = await service.get_all_paged(skip=0, limit=10)

        assert result["total"] == 1
        assert len(result["items"]) == 1
        mock_repo.get_all.assert_called_once()
        mock_repo.count.assert_called_once()

    async def test_add_lokasyon_simple(self, service, mock_repo):
        data = LokasyonCreate(
            cikis_yeri="İstanbul",
            varis_yeri="Ankara",
            mesafe_km=450,
            tahmini_sure_saat=5.0,
            zorluk="Normal",
        )
        mock_repo.get_by_route.return_value = None
        mock_repo.add.return_value = 1

        result = await service.add_lokasyon(data)

        assert result == 1
        mock_repo.add.assert_called_once()
        # Ensure it didn't try to fetch route details (no coords)
        # analyze_route assertion is difficult here without mocking inside add_lokasyon check
        # but since coords are missing it shouldn't trigger analysis.

    @patch.object(LokasyonService, "analyze_route")
    async def test_add_lokasyon_with_coords_triggers_analysis(
        self, mock_analyze, service, mock_repo
    ):
        data = LokasyonCreate(
            cikis_yeri="İstanbul",
            varis_yeri="Kocaeli",
            mesafe_km=100,
            cikis_lat=41.0,
            cikis_lon=29.0,
            varis_lat=40.8,
            varis_lon=29.4,
        )
        mock_repo.get_by_route.return_value = None
        mock_repo.add.return_value = 5

        await service.add_lokasyon(data)

        mock_repo.add.assert_called_once()
        mock_analyze.assert_called_once_with(5)

    async def test_update_lokasyon(self, service, mock_repo):
        data = LokasyonUpdate(mesafe_km=500, notlar="Updated Info")
        mock_repo.update.return_value = True

        result = await service.update_lokasyon(1, data)

        assert result is True
        mock_repo.update.assert_called_once()

    async def test_delete_lokasyon_soft(self, service, mock_repo):
        # Case 1: Active location -> Soft Delete
        mock_repo.get_by_id.return_value = {"id": 1, "aktif": True}
        mock_repo.update.return_value = True

        result = await service.delete_lokasyon(1)

        assert result is True
        mock_repo.update.assert_called_once_with(1, aktif=False)

    async def test_delete_lokasyon_hard(self, service, mock_repo):
        # Case 2: Inactive location -> Hard Delete
        mock_repo.get_by_id.return_value = {"id": 1, "aktif": False}
        mock_repo.hard_delete.return_value = True

        result = await service.delete_lokasyon(1)

        assert result is True
        mock_repo.hard_delete.assert_called_once_with(1)
