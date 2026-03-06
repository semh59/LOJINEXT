"""
Unit Tests - SeferService
"""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError


class TestSeferService:
    """Test suite for SeferService."""

    def test_service_singleton(self, sefer_service):
        """Service should return singleton instance."""
        from app.core.services.sefer_service import get_sefer_service

        service2 = get_sefer_service()
        assert sefer_service is service2

    @pytest.mark.asyncio
    async def test_get_all_trips_returns_list(self, sefer_service):
        """get_all_trips should return a list."""
        trips = await sefer_service.get_all_trips()
        assert isinstance(trips, list)

    @pytest.mark.asyncio
    async def test_get_all_trips_with_limit(self, sefer_service):
        """Limit parameter should work correctly."""
        trips = await sefer_service.get_all_trips(limit=5)
        assert len(trips) <= 5

    @pytest.mark.asyncio
    async def test_get_all_trips_with_date_filter(self, sefer_service):
        """Date filters should be applied."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Pass date objects, not strings (isoformat removed)
        trips = await sefer_service.get_all_trips(start_date=yesterday, end_date=today)
        assert isinstance(trips, list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", ["Bekliyor", "Yolda", "Tamam", None])
    async def test_get_all_trips_status_filter(self, sefer_service, status):
        """Status filter should work for all valid statuses."""
        trips = await sefer_service.get_all_trips(status=status)
        assert isinstance(trips, list)


class TestSeferServiceValidation:
    """Test input validation in SeferService."""

    def test_add_sefer_requires_arac_id(self, sefer_service, sample_sefer_data):
        """Adding a trip without arac_id should fail."""
        # SeferCreate validation handles this, so we expect ValidationError
        from app.core.entities.models import SeferCreate

        data = sample_sefer_data.copy()
        data.pop("arac_id")

        with pytest.raises(ValidationError):
            SeferCreate(**data)

    def test_add_sefer_requires_locations(self, sefer_service, sample_sefer_data):
        """Adding a trip without locations should fail."""
        from app.core.entities.models import SeferCreate

        data = sample_sefer_data.copy()
        data["cikis_yeri"] = ""
        data["varis_yeri"] = ""

        with pytest.raises(ValidationError):
            SeferCreate(**data)

    @pytest.mark.asyncio
    async def test_add_sefer_same_locations(self, sefer_service, sample_sefer_data):
        """Start and end location cannot be the same."""
        from app.core.entities.models import SeferCreate

        data = sample_sefer_data.copy()
        data["cikis_yeri"] = "İstanbul"
        data["varis_yeri"] = "İstanbul"

        # This is a business rule in service, not necessarily model validation (unless model validtor exists)
        # Service throws ValueError
        model = SeferCreate(**data)
        with pytest.raises(ValueError, match="Çıkış ve varış yeri aynı olamaz"):
            await sefer_service.add_sefer(model)


class TestSeferServiceStats:
    """Test statistics methods in SeferService."""

    @pytest.mark.asyncio
    async def test_get_bugunun_seferleri(self, sefer_service):
        """Today's trips should be retrievable."""
        # This method is in repository, maybe not exposed directly in service but db_manager has it.
        # But ReportService handles stats usually.
        # However, checking repo directly for unit test is acceptable for verifying DB query logic.
        trips = await sefer_service.repo.get_bugunun_seferleri()
        assert isinstance(trips, list)

        # All trips should have today's date
        today = date.today().isoformat()
        for trip in trips:
            trip_date = trip.get("tarih") if isinstance(trip, dict) else trip.tarih
            assert str(trip_date) == today
