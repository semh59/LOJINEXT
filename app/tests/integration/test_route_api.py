import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.routing.openroute_client import OpenRouteClient


@pytest.fixture
def mock_ors_response():
    return {
        "routes": [
            {
                "summary": {
                    "distance": 100000.0,  # 100km
                    "duration": 3600.0,  # 1h
                    "ascent": 500.0,
                    "descent": 400.0,
                },
                "geometry": "encoded_polyline_string",  # We'll mock decode anyway
                "extras": {
                    "steepness": {"values": [[0, 10, 0]]},
                    "waycategory": {"values": [[0, 10, 1]]},
                },
            }
        ]
    }


@pytest.mark.asyncio
async def test_openroute_client_structure(mock_ors_response):
    # Test that the client can be instantiated and methods called

    # Mock dependencies
    with patch("app.database.connection.get_sync_session") as mock_session_ctx:
        # Create a mock session
        mock_session = MagicMock()
        mock_session_ctx.return_value.__enter__.return_value = mock_session

        # Mock API call
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_ors_response

            # Mock Polyline Decoder to return dummy points
            with patch("app.core.utils.polyline.PolylineDecoder.decode") as mock_decode:
                mock_decode.return_value = [(0, 0), (1, 1)]

                # Mock Route Analyzer
                with patch(
                    "app.domain.services.route_analyzer.RouteAnalyzer.analyze_segments"
                ) as mock_analyze:
                    mock_analyze.return_value = {"highway": {"flat": 100.0}}

                    client = OpenRouteClient(api_key="test_key")
                    # Use valid coordinates (Turkey)
                    result = client.get_distance(
                        (40.0, 30.0),
                        (41.0, 31.0),
                        use_cache=False,
                        include_details=True,
                    )

                    assert result is not None
                    assert result["distance_km"] == 100.0
                    assert result["details"]["highway"]["flat"] == 100.0


@pytest.mark.asyncio
async def test_update_route_distance_log(mock_ors_response):
    # Verify that update_route_distance attempts to update the database

    # We need to mock the session interaction heavily since we are not using a real DB in this unit/integration hybrid
    # For true integration we'd need a real DB, but let's stick to checking the logic flow first.

    with patch("app.database.connection.get_sync_session") as mock_session_ctx:
        mock_session = MagicMock()
        mock_session_ctx.return_value.__enter__.return_value = mock_session

        # Mock SELECT response for getting coordinates
        mock_row = MagicMock()
        mock_row.cikis_lat = 40.0
        mock_row.cikis_lon = 29.0
        mock_row.varis_lat = 41.0
        mock_row.varis_lon = 29.0
        mock_session.execute.return_value.fetchone.return_value = mock_row

        # Mock API
        with patch(
            "app.infrastructure.routing.openroute_client.OpenRouteClient.get_distance"
        ) as mock_get_dist:
            mock_get_dist.return_value = {
                "distance_km": 100,
                "duration_hours": 1,
                "ascent_m": 10,
                "descent_m": 10,
                "details": {"test": "data"},
            }

            client = OpenRouteClient(api_key="test")
            client.update_route_distance(123)

            # Verify get_distance was called with include_details=True
            mock_get_dist.assert_called_with(
                (40.0, 29.0), (41.0, 29.0), use_cache=False, include_details=True
            )

            # Verify UPDATE was called
            # We check if session.execute was called with an UPDATE statement
            calls = mock_session.execute.call_args_list
            # First call is SELECT, second (or third depending on logic) should be UPDATE

            update_called = False
            for call in calls:
                args, _ = call
                if "UPDATE lokasyonlar" in str(args[0]):
                    update_called = True
                    break

            assert update_called, "UPDATE statement was not executed"
