"""
Unit Tests - YakitService
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestYakitService:
    """Test suite for YakitService."""

    def test_service_singleton(self, yakit_service):
        """Service should return singleton instance."""
        from app.core.services.yakit_service import get_yakit_service

        service2 = get_yakit_service()
        assert yakit_service is service2, (
            "get_yakit_service should return the same instance"
        )

    @pytest.mark.asyncio
    async def test_get_all_fuel_records_returns_list(self, yakit_service):
        """get_all should return a list."""
        records = await yakit_service.get_all()
        assert isinstance(records, list), "get_all should return a list"
        # If records exist, verify structure
        if records:
            assert hasattr(records[0], "id") or "id" in records[0]

    @pytest.mark.asyncio
    async def test_get_by_vehicle_id(self, yakit_service):
        """Should filter by vehicle ID."""
        records = await yakit_service.get_all()
        if not records:
            pytest.skip("No records found to test filtering")

        vehicle_id = records[0].arac_id if hasattr(records[0], "arac_id") else 1
        filtered = await yakit_service.get_by_vehicle(vehicle_id)

        assert isinstance(filtered, list), "Filtered result should be a list"
        for record in filtered:
            r_arac_id = (
                record.arac_id if hasattr(record, "arac_id") else record.get("arac_id")
            )
            assert r_arac_id == vehicle_id, (
                f"Record should belong to vehicle {vehicle_id}"
            )


class TestYakitServiceValidation:
    """Test input validation in YakitService."""

    @pytest.mark.asyncio
    async def test_add_fuel_requires_vehicle(self, yakit_service, sample_yakit_data):
        """Adding fuel without vehicle should fail."""
        data = sample_yakit_data.copy()
        if "arac_id" in data:
            data.pop("arac_id")

        # Expect specific ValidationError or ValueError
        with pytest.raises((ValueError, TypeError, KeyError), match="arac_id"):
            await yakit_service.add_yakit_alimi(**data)

    @pytest.mark.asyncio
    async def test_add_fuel_requires_positive_litre(
        self, yakit_service, sample_yakit_data
    ):
        """Litre must be positive."""
        data = sample_yakit_data.copy()
        data["litre"] = -50

        with pytest.raises(ValueError, match="litre"):
            await yakit_service.add_yakit_alimi(**data)

    @pytest.mark.asyncio
    async def test_add_fuel_future_date_check(self, yakit_service, sample_yakit_data):
        """Future date should be prevented if logic exists."""
        from datetime import timedelta

        data = sample_yakit_data.copy()
        data["tarih"] = date.today() + timedelta(days=365)

        # Taking a guess that service prevents future dates, if not it might pass or fail.
        # Based on integration tests, it seems it raises ValueError.
        with pytest.raises(ValueError):
            await yakit_service.add_yakit_alimi(**data)


class TestYakitServiceStats:
    """Test statistics methods in YakitService."""

    @pytest.mark.asyncio
    async def test_get_yakit_stats(self, yakit_service, monkeypatch):
        """Should return summary stats."""
        mock_analiz = AsyncMock()
        mock_analiz.get_dashboard_stats.return_value = {
            "toplam_yakit": 5000,
            "filo_ortalama": 32.5,
            "toplam_tutar": 200000,
        }
        monkeypatch.setattr(
            "app.core.services.yakit_service.get_yakit_repo", lambda: MagicMock()
        )
        monkeypatch.setattr(
            "app.database.repositories.analiz_repo.get_analiz_repo", lambda: mock_analiz
        )

        stats = await yakit_service.get_stats()

        assert stats["toplam_yakit"] == 5000
        assert stats["aylik_ort"] == 32.5

    @pytest.mark.asyncio
    async def test_get_monthly_summary(self, yakit_service, monkeypatch):
        """Should return monthly consumption series."""
        mock_analiz = AsyncMock()
        mock_analiz.get_monthly_consumption_series.return_value = [
            {"month": "Oca", "consumption": 1000}
        ]
        monkeypatch.setattr(
            "app.database.repositories.analiz_repo.get_analiz_repo", lambda: mock_analiz
        )

        summary = await yakit_service.get_monthly_summary()

        assert isinstance(summary, list)
        assert len(summary) == 1
        assert summary[0]["month"] == "Oca"
        assert summary[0]["consumption"] == 1000
