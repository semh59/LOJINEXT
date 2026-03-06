import pytest
from unittest.mock import AsyncMock, MagicMock
from app.database.repositories.sefer_repo import SeferRepository
from app.database.repositories.arac_repo import AracRepository

# Mark as async test
pytestmark = pytest.mark.asyncio


async def test_get_cost_leakage_stats_logic():
    """
    Test SeferRepository.get_cost_leakage_stats calculation logic.
    Mocking the DB execution to verify math.
    """
    repo = SeferRepository()
    repo._get_session = MagicMock()
    mock_session = AsyncMock()
    repo._get_session.return_value.__aenter__.return_value = mock_session

    # Mock DB Results
    # Route: 100km total deviation
    # Fuel: 50L total gap
    mock_route_result = MagicMock()
    mock_route_result.scalar.return_value = 100.0

    mock_fuel_result = MagicMock()
    mock_fuel_result.scalar.return_value = 50.0

    mock_session.execute.side_effect = [mock_route_result, mock_fuel_result]

    stats = await repo.get_cost_leakage_stats(days=30)

    # Constants from Repo:
    # EST_KM_COST = 13.5
    # AVG_FUEL_PRICE = 42.0

    expected_route_cost = 100.0 * 13.5
    expected_fuel_cost = 50.0 * 42.0
    expected_total = expected_route_cost + expected_fuel_cost

    assert stats["route_deviation_km"] == 100.0
    assert stats["fuel_gap_liters"] == 50.0
    assert stats["route_deviation_cost"] == expected_route_cost
    assert stats["fuel_gap_cost"] == expected_fuel_cost
    assert stats["total_leakage_cost"] == expected_total


async def test_get_maintenance_candidates_logic():
    """
    Test AracRepository.get_maintenance_candidates logic.
    """
    repo = AracRepository()
    repo.execute_query = AsyncMock()

    # Mock Data:
    # 1. Old Vehicle (2000 model) -> Age 24 (>15)
    # 2. High Consumption (40L) -> >35
    # 3. Both
    # 4. None
    mock_rows = [
        {"id": 1, "plaka": "34 OLD 01", "yil": 2000, "ort_tuketim": 30.0},  # Age only
        {"id": 2, "plaka": "34 GAS 02", "yil": 2020, "ort_tuketim": 40.0},  # Fuel only
        {"id": 3, "plaka": "34 BAD 03", "yil": 2000, "ort_tuketim": 40.0},  # Both
    ]
    repo.execute_query.return_value = mock_rows

    result = await repo.get_maintenance_candidates()

    # Vehicle 3 should be High severity (2 reasons)
    # Vehicles 1 and 2 should be Medium (1 reason)

    assert result["urgent_count"] == 1  # Only #3
    assert result["warning_count"] == 2  # #1 and #2
    assert len(result["vehicles"]) == 3

    v3 = next(v for v in result["vehicles"] if v["id"] == 3)
    assert v3["severity"] == "high"
    assert "Yaşlı Araç" in v3["reason"]
    assert "Yüksek Tüketim" in v3["reason"]
