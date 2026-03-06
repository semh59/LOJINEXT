import pytest
from datetime import date

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USER = "skara"
ADMIN_PASS = "!23efe25ali!"


@pytest.mark.asyncio
async def test_security_payloads_add_fuel(async_client, async_superuser_token_headers):
    """
    Security Test: Injection attempts.
    """
    headers = async_superuser_token_headers

    # 1. Get active vehicle
    arac_res = await async_client.get(
        "/api/v1/vehicles/", headers=headers, params={"aktif_only": True}
    )
    arac_data = arac_res.json()
    if not arac_data:
        # Create a vehicle
        v_res = await async_client.post(
            "/api/v1/vehicles/",
            headers=headers,
            json={
                "plaka": "34-SEC-01",
                "marka": "Security",
                "model": "Test",
                "yil": 2020,
                "tank_kapasitesi": 100,
                "hedef_tuketim": 30.0,
                "aktif": True,
            },
        )
        assert v_res.status_code in [200, 201]
        target_arac_id = v_res.json()["id"]
    else:
        target_arac_id = arac_data[0]["id"]

    # 2. SQL Injection
    payload_sqli = {
        "tarih": date.today().isoformat(),
        "arac_id": target_arac_id,
        "istasyon": "Station'; DROP TABLE users; --",
        "fiyat_tl": 40.0,
        "litre": 10.0,
        "km_sayac": 900000,
        "fis_no": "SQLI-TEST",
        "depo_durumu": "Full",
    }
    res = await async_client.post("/api/v1/fuel/", json=payload_sqli, headers=headers)

    assert res.status_code in [200, 201, 422, 400]
    if res.status_code in [200, 201]:
        data = res.json()
        assert "DROP TABLE" in data["istasyon"]

    # 3. XSS
    payload_xss = payload_sqli.copy()
    payload_xss["istasyon"] = "Normal Station"
    payload_xss["fis_no"] = "<script>alert('XSS')</script>"
    res_xss = await async_client.post(
        "/api/v1/fuel/", json=payload_xss, headers=headers
    )

    assert res_xss.status_code in [200, 201, 422, 400]
    if res_xss.status_code in [200, 201]:
        data = res_xss.json()
        assert "<script>" in data["fis_no"]


@pytest.mark.asyncio
async def test_validation_boundaries(async_client, async_superuser_token_headers):
    """
    Validation Test: Negative numbers.
    """
    headers = async_superuser_token_headers

    arac_res = await async_client.get(
        "/api/v1/vehicles/", headers=headers, params={"aktif_only": True}
    )
    arac_data = arac_res.json()
    if not arac_data:
        # Create a vehicle
        v_res = await async_client.post(
            "/api/v1/vehicles/",
            headers=headers,
            json={
                "plaka": "34-BOUND-01",
                "marka": "Boundary",
                "model": "Test",
                "yil": 2020,
                "tank_kapasitesi": 100,
                "hedef_tuketim": 30.0,
                "aktif": True,
            },
        )
        assert v_res.status_code in [200, 201]
        target_arac_id = v_res.json()["id"]
    else:
        target_arac_id = arac_data[0]["id"]

    # Negative Price
    p_neg = {
        "tarih": date.today().isoformat(),
        "arac_id": target_arac_id,
        "istasyon": "Neg Station",
        "fiyat_tl": -50.0,
        "litre": 10.0,
        "km_sayac": 999999,
        "fis_no": "NEG-1",
        "depo_durumu": "Full",
    }
    res = await async_client.post("/api/v1/fuel/", json=p_neg, headers=headers)
    assert res.status_code in [400, 422]

    # Zero Listre
    p_zero = p_neg.copy()
    p_zero["fiyat_tl"] = 40.0
    p_zero["litre"] = 0.0
    res = await async_client.post("/api/v1/fuel/", json=p_zero, headers=headers)
    assert res.status_code in [400, 422]
