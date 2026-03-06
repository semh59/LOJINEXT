import pytest
from app.infrastructure.routing.mapbox_client import MapboxClient
from app.config import settings


@pytest.mark.asyncio
class TestMapboxClientIntegration:
    async def test_mapbox_get_route_success(self):
        """Test real Mapbox connection (if key is present)"""
        if not settings.MAPBOX_API_KEY:
            pytest.skip("Mapbox API Key not set in environment")

        client = MapboxClient()
        # Istanbul coordinates (Eminönü -> Taksim)
        start = (28.9784, 41.0082)
        end = (28.9850, 41.0370)

        result = await client.get_route(start, end)

        assert result is not None
        assert "distance_km" in result
        assert "duration_min" in result
        assert result["distance_km"] > 0
        assert result["source"] == "mapbox_smart_fallback"

    async def test_mapbox_get_route_no_key(self, monkeypatch):
        """Should return None if API key is missing"""
        monkeypatch.setattr(settings, "MAPBOX_API_KEY", None)
        client = MapboxClient()
        # Use simple coords
        result = await client.get_route((0, 0), (1, 1))
        assert result is None
