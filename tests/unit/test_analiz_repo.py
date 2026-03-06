import pytest
from unittest.mock import MagicMock, AsyncMock
from app.database.repositories.analiz_repo import (
    AnalizRepository,
    DEFAULT_FILO_ORTALAMA,
)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return AnalizRepository(session=mock_session)


@pytest.mark.asyncio
async def test_get_dashboard_stats_success(repo, mock_session):
    # Mock result row (supporting dot notation and float conversion)
    from types import SimpleNamespace

    mock_row = SimpleNamespace(
        toplam_sefer=100,
        toplam_km=5000.0,
        toplam_yakit=1500.5,
        filo_ortalama=30.0,
        aktif_arac=10,
        toplam_arac=12,
        aktif_sofor=8,
        bugun_sefer=5,
    )

    # Mock execute result
    mock_result = MagicMock()
    mock_result.fetchone.return_value = mock_row
    mock_session.execute.return_value = mock_result

    from datetime import date

    today = date.today()
    stats = await repo.get_dashboard_stats(today_utc=today)

    assert stats["toplam_sefer"] == 100
    assert stats["filo_ortalama"] == 30.0
    assert stats["toplam_yakit"] == 1500.5

    # Verify query execution
    mock_session.execute.assert_called_once()
    args, kwargs = mock_session.execute.call_args
    assert "default_ortalama" in args[1]
    assert args[1]["default_ortalama"] == DEFAULT_FILO_ORTALAMA


@pytest.mark.asyncio
async def test_get_dashboard_stats_empty(repo, mock_session):
    # Mock empty result
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_session.execute.return_value = mock_result

    from datetime import date

    stats = await repo.get_dashboard_stats(today_utc=date.today())

    assert stats == {
        "toplam_sefer": 0,
        "toplam_km": 0,
        "toplam_yakit": 0,
        "filo_ortalama": DEFAULT_FILO_ORTALAMA,
        "aktif_arac": 0,
        "toplam_arac": 0,
        "aktif_sofor": 0,
        "bugun_sefer": 0,
    }


@pytest.mark.asyncio
async def test_get_filo_ortalama_tuketim_default(repo, mock_session):
    # Mock None result (no data)
    repo.execute_scalar = AsyncMock(return_value=None)

    val = await repo.get_filo_ortalama_tuketim()

    assert val == DEFAULT_FILO_ORTALAMA


@pytest.mark.asyncio
async def test_get_filo_ortalama_tuketim_value(repo, mock_session):
    # Mock real value
    repo.execute_scalar = AsyncMock(return_value=28.543)

    val = await repo.get_filo_ortalama_tuketim()

    assert val == 28.54  # Rounded to 2 digits


@pytest.mark.asyncio
async def test_get_all_vehicles_consumption_stats(repo, mock_session):
    # Mock fetchall result
    mock_row = MagicMock()
    mock_row._mapping = {
        "arac_id": 1,
        "plaka": "34ABC12",
        "hedef_tuketim": 30,
        "sefer_sayisi": 5,
        "ort_tuketim": 32.5,
        "son_15_gun_ort": 33.0,
        "onceki_15_gun_ort": 31.0,
    }

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]
    mock_session.execute.return_value = mock_result

    stats = await repo.get_all_vehicles_consumption_stats(days=30)

    assert len(stats) == 1
    assert stats[0]["plaka"] == "34ABC12"
    assert stats[0]["ort_tuketim"] == 32.5
