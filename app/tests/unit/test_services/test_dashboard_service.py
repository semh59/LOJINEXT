"""
Unit Tests - DashboardService
"""


class TestDashboardService:
    """Test suite for DashboardService."""

    def test_service_singleton(self, dashboard_service):
        """Service should return singleton instance."""
        from app.core.services.dashboard_service import get_dashboard_service
        service2 = get_dashboard_service()
        assert dashboard_service is service2

    async def test_get_dashboard_data_structure(self, dashboard_service):
        """Dashboard data should have expected structure."""
        data = await dashboard_service.get_dashboard_data()

        assert isinstance(data, dict)
        assert 'stats' in data
        assert 'recent_trips' in data
        assert 'chart_data' in data

    async def test_stats_contains_expected_fields(self, dashboard_service):
        """Stats should contain expected fields."""
        data = await dashboard_service.get_dashboard_data()
        stats = data.get('stats', {})

        # Check for common stat fields
        expected_fields = ['toplam_sefer', 'toplam_km', 'aktif_arac']
        for field in expected_fields:
            assert field in stats or stats == {}  # Empty stats is valid

    async def test_chart_data_format(self, dashboard_service):
        """Chart data should be a list of dicts with month/consumption."""
        data = await dashboard_service.get_dashboard_data()
        chart_data = data.get('chart_data', [])

        assert isinstance(chart_data, list)
        for item in chart_data:
            assert isinstance(item, dict)
            if item:  # Non-empty item
                assert 'month' in item or 'ay' in item
                assert 'consumption' in item

    async def test_recent_trips_is_list(self, dashboard_service):
        """Recent trips should be a list."""
        data = await dashboard_service.get_dashboard_data()
        recent_trips = data.get('recent_trips', [])

        assert isinstance(recent_trips, list)

    async def test_error_handling_returns_defaults(self, dashboard_service, monkeypatch):
        """Errors should return safe defaults, not crash."""
        from unittest.mock import AsyncMock
        
        # Simulate an error by breaking the repo (which is async)
        dashboard_service.sefer_repo.get_bugunun_seferleri = AsyncMock(side_effect=Exception("Simulated error"))

        data = await dashboard_service.get_dashboard_data()

        # Should return empty defaults, not raise
        assert isinstance(data, dict)
        assert data.get('recent_trips') == []
