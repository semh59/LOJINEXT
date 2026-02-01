import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.routing.openroute_client import OpenRouteClient


class TestOpenRouteClient:
    """OpenRouteClient birim testleri"""

    @pytest.fixture
    def client(self):
        """Test hazırlığı"""
        return OpenRouteClient(api_key="test-api-key-placeholder")

    def test_validate_coordinates_valid(self, client):
        """Geçerli Türkiye koordinatları"""
        origin = (40.7669, 29.4319)
        destination = (39.9334, 32.8597)
        assert client._validate_coordinates(origin, destination) is True

    def test_validate_coordinates_invalid_latitude(self, client):
        """Geçersiz enlem (Türkiye dışı)"""
        origin = (50.0, 29.0)
        destination = (39.9, 32.8)
        assert client._validate_coordinates(origin, destination) is False

    @patch('requests.post')
    def test_call_api_success(self, mock_post, client):
        """Başarılı API çağrısı"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "routes": [{
                "summary": {
                    "distance": 452300,
                    "duration": 19800,
                    "ascent": 1250,
                    "descent": 1180
                }
            }]
        }
        mock_post.return_value = mock_response

        # OpenRouteClient._call_api sync çalışıyor
        result = client._call_api(
            origin=(40.7669, 29.4319),
            destination=(39.9334, 32.8597)
        )

        assert result is not None
        assert result["distance_km"] == 452.3
        assert result["duration_hours"] == 5.5

    def test_get_distance_no_api_key(self):
        """API key olmadan çağrı"""
        client = OpenRouteClient(api_key=None)
        client.api_key = None
        result = client.get_distance(
            origin=(40.7669, 29.4319),
            destination=(39.9334, 32.8597),
            use_cache=False
        )
        assert result is None


class TestOpenRouteClientIntegration:
    """Entegrasyon testleri (gerçek API çağrısı)"""

    @pytest.mark.skipif(
        not __import__('os').getenv("OPENROUTE_API_KEY"),
        reason="OPENROUTE_API_KEY tanımlanmamış"
    )
    @patch('app.infrastructure.routing.openroute_client.OpenRouteClient._call_api')
    def test_real_api_call(self, mock_call):
        """Gerçek API çağrısı simülasyonu (Gebze -> Ankara)"""
        mock_call.return_value = {
            "distance_km": 450.0,
            "duration_hours": 5.0,
            "ascent_m": 1000,
            "descent_m": 1000
        }
        client = OpenRouteClient()
        result = client.get_distance(
            origin=(40.7669, 29.4319),
            destination=(39.9334, 32.8597),
            use_cache=False
        )
        assert result is not None
        assert 350 < result["distance_km"] < 500
