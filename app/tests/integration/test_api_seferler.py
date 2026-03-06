import uuid
from datetime import date

import pytest


@pytest.mark.asyncio
class TestSeferAPI:
    """Sefer API Entegrasyon Testleri (Elite)"""

    async def test_sefer_lifecycle_full_flow(self, async_client, admin_auth_headers):
        unique_suffix = uuid.uuid4().hex[:4].upper()

        # 1. SETUP: Create Arac
        plaka = f"34 AB {int(uuid.uuid4().hex[:4], 16) % 10000:04d}"
        arac_payload = {
            "plaka": plaka,
            "marka": "Mercedes",
            "model": "Actros",
            "yil": 2023,
            "tank_kapasitesi": 600,
            "hedef_tuketim": 31.5,
            "aktif": True,
        }
        resp_arac = await async_client.post(
            "/api/v1/vehicles/", json=arac_payload, headers=admin_auth_headers
        )
        assert resp_arac.status_code == 201, f"Arac create failed: {resp_arac.text}"
        arac_id = resp_arac.json()["id"]

        # 2. SETUP: Create Sofor
        sofor_payload = {
            "ad_soyad": f"Test Pilot {unique_suffix}",
            "telefon": "05550000000",
            "ise_baslama": date.today().isoformat(),
            "ehliyet_sinifi": "E",
            "aktif": True,
        }
        resp_sofor = await async_client.post(
            "/api/v1/drivers/", json=sofor_payload, headers=admin_auth_headers
        )
        assert resp_sofor.status_code == 201, f"Sofor create failed: {resp_sofor.text}"
        sofor_id = resp_sofor.json()["id"]

        # 3. SETUP: Create Lokasyon (Required for Sefer)
        lokasyon_payload = {
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450.0,
            "tahmini_sure_saat": 5.0,
            "zorluk": "Normal",
            "notlar": f"Rota {unique_suffix}",
        }
        resp_loc = await async_client.post(
            "/api/v1/locations/", json=lokasyon_payload, headers=admin_auth_headers
        )
        assert resp_loc.status_code == 201, f"Location create failed: {resp_loc.text}"
        lokasyon_id = resp_loc.json()["id"]

        # 4. ACTION: Create Sefer
        sefer_payload = {
            "tarih": date.today().isoformat(),
            "arac_id": arac_id,
            "sofor_id": sofor_id,
            "guzergah_id": lokasyon_id,
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450.0,
            "net_kg": 22000,
            "bos_sefer": False,
            "durum": "Tamam",
        }
        resp_sefer = await async_client.post(
            "/api/v1/trips/", json=sefer_payload, headers=admin_auth_headers
        )

        # Verify 201 Created
        assert resp_sefer.status_code == 201, f"Trip create failed: {resp_sefer.text}"
        sefer_data = resp_sefer.json()
        sefer_id = sefer_data["id"]
        assert isinstance(sefer_id, int)

        # 5. VERIFY: Retrieve Sefer
        resp_get = await async_client.get(
            f"/api/v1/trips/{sefer_id}", headers=admin_auth_headers
        )
        assert resp_get.status_code == 200
        data = resp_get.json()
        assert data["cikis_yeri"] == "Istanbul"
        assert data["arac_id"] == arac_id
        assert data["guzergah_id"] == lokasyon_id

        # 6. ACTION: Update Sefer
        update_payload = {"mesafe_km": 460.0, "notlar": "Rota degisikligi"}
        resp_update = await async_client.put(
            f"/api/v1/trips/{sefer_id}", json=update_payload, headers=admin_auth_headers
        )
        assert resp_update.status_code == 200

        # 7. VERIFY: Updated Data
        resp_verify = await async_client.get(
            f"/api/v1/trips/{sefer_id}", headers=admin_auth_headers
        )
        assert resp_verify.json()["mesafe_km"] == 460.0

        # 8. ACTION: Delete Sefer
        resp_delete = await async_client.delete(
            f"/api/v1/trips/{sefer_id}", headers=admin_auth_headers
        )
        assert resp_delete.status_code == 200

        # 9. FINAL VERIFY: Gone
        resp_final = await async_client.get(
            f"/api/v1/trips/{sefer_id}", headers=admin_auth_headers
        )
        assert resp_final.status_code == 404

    async def test_create_sefer_invalid_arac(self, async_client, admin_auth_headers):
        """Olmayan araç için sefer oluşturma hatası (400)"""
        sefer_payload = {
            "tarih": date.today().isoformat(),
            "arac_id": 999999,
            "sofor_id": 1,
            "guzergah_id": 1,
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450.0,
        }
        resp = await async_client.post(
            "/api/v1/trips/", json=sefer_payload, headers=admin_auth_headers
        )
        assert resp.status_code == 400
