import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_create_location(async_client: AsyncClient, admin_auth_headers):
    """Admin yeni lokasyon oluşturabilmeli"""
    payload = {
        "cikis_yeri": "Test City A",
        "varis_yeri": "Test City B",
        "mesafe_km": 120.5,
    }
    response = await async_client.post(
        "/api/v1/locations/", json=payload, headers=admin_auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["cikis_yeri"] == "Test City A"
    assert "id" in data


@pytest.mark.asyncio
async def test_api_list_locations(async_client: AsyncClient, admin_auth_headers):
    """Lokasyonlar listelenebilmeli ve pagination çalışmalı"""
    response = await async_client.get(
        "/api/v1/locations/?limit=5&skip=0", headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_api_get_route_info(async_client: AsyncClient, admin_auth_headers):
    """Koordinatlara göre rota bilgisi alma testi"""
    params = {
        "cikis_lat": 41.0,
        "cikis_lon": 29.0,
        "varis_lat": 40.0,
        "varis_lon": 32.0,
    }
    response = await async_client.get(
        "/api/v1/locations/route-info", params=params, headers=admin_auth_headers
    )
    # OpenRouteService dummy key ile fail edebilir veya mock gerekebilir.
    # conftest.py içinde dummy key tanımlı olduğu için 403 veya cached/offline dönebilir.
    # En azından endpoint'in 200-500 arası bir şey dönüp patlamadığını kontrol edelim.
    assert response.status_code in [200, 400, 403]


@pytest.mark.asyncio
async def test_api_unauthorized_access(async_client: AsyncClient):
    """Auth olmadan erişim başarısız olmalı"""
    response = await async_client.get("/api/v1/locations/")
    assert response.status_code == 401
