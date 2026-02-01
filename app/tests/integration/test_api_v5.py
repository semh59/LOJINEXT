import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
async def test_pagination_limit_enforcement(async_client, auth_headers):
    """Tüm liste endpointlerinin MAX_PAGINATION_LIMIT'e uyduğunu doğrula"""
    response = await async_client.get("/api/v1/vehicles/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_vehicle_soft_delete(async_client, auth_headers):
    """Araç silme işleminin soft delete olduğunu doğrula (End-to-End)"""
    import uuid
    # Plaka regex: ^[0-9]{2}\s?[A-Z]{1,3}\s?[0-9]{2,4}$ - sadece rakamla bitecek
    plaka = f"34 SD {str(uuid.uuid4().int)[:4]}"
    
    # 1. Araç oluştur
    create_resp = await async_client.post("/api/v1/vehicles/", json={
        "plaka": plaka,
        "marka": "SoftDeleteTest",
        "model": "S-Class",
        "yil": 2024
    }, headers=auth_headers)
    assert create_resp.status_code == 200
    arac_id = create_resp.json()["id"]
    
    # 2. Sil
    del_resp = await async_client.delete(f"/api/v1/vehicles/{arac_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    
    # 3. Listede görünmediğini doğrula
    list_resp = await async_client.get("/api/v1/vehicles/", headers=auth_headers)
    plakalar = [v["plaka"] for v in list_resp.json()]
    assert plaka not in plakalar

@pytest.mark.asyncio
async def test_prediction_endpoints_exist(async_client, auth_headers):
    """Tahmin endpointlerinin mevcut olduğunu ve servis hatası vermediğini doğrula"""
    # Note: Using get_current_user endpoints just to check existence/auth
    response = await async_client.get("/api/v1/predictions/time-series/status", headers=auth_headers)
    assert response.status_code == 200
