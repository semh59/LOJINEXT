import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.routing.openroute_client import OpenRouteClient


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def client():
    return OpenRouteClient(api_key="mock_key")


def test_update_route_distance_parses_details(client, mock_session):
    # Setup
    lokasyon_id = 999

    # Mock return from get_distance (simulation of OK response from API)
    mock_api_result = {
        "distance_km": 100.0,
        "duration_hours": 1.5,
        "ascent_m": 500,
        "descent_m": 500,
        "details": {
            "highway": {"flat": 40.0, "up": 10.0, "down": 10.0},  # Total 60
            "other": {"flat": 20.0, "up": 10.0, "down": 10.0},  # Total 40
        },
    }

    # We need to mock get_sync_session
    # It is imported inside the method, so we patch where it is defined
    with patch("app.database.connection.get_sync_session") as mock_get_session:
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock fetchone to return coordinates
        mock_row = MagicMock()
        mock_row.cikis_lat = 40.0
        mock_row.cikis_lon = 29.0
        mock_row.varis_lat = 39.0
        mock_row.varis_lon = 32.0
        mock_session.execute.return_value.fetchone.return_value = mock_row

        # Mock the internal get_distance call
        with patch.object(client, "get_distance", return_value=mock_api_result):
            # Execute
            result = client.update_route_distance(lokasyon_id)

            # Verify result
            assert result == mock_api_result

            # Verify SQL update params
            # The second call to execute should be the UPDATE
            # 1st call: SELECT coords
            # 2nd call: UPDATE
            assert mock_session.execute.call_count == 2

            args, kwargs = mock_session.execute.call_args_list[1]
            sql = args[0]
            params = args[1]

            # Assertions
            str_sql = str(sql)
            assert "otoban_mesafe_km = :otoban" in str_sql
            assert "sehir_ici_mesafe_km = :sehir" in str_sql

            assert params["otoban"] == 60.0
            assert params["sehir"] == 40.0
            assert params["id"] == lokasyon_id
