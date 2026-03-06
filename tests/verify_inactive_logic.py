import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"


async def test_inactive_logic():
    print("\n--- PASİF ARAÇ VE ŞOFÖR KONTROLÜ TESTİ BAŞLATILIYOR ---")

    async with httpx.AsyncClient() as client:
        # 1. Login
        print("\n[1] Giriş yapılıyor...")
        resp = await client.post(
            f"{BASE_URL}/auth/token",
            data={
                "username": "skara",
                "password": "!23efe25ali!",
                "grant_type": "password",
            },
            timeout=30.0,
        )

        if resp.status_code != 200:
            print(f"❌ Giriş başarısız! Kod: {resp.status_code}")
            print(resp.text)
            return

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Giriş başarılı.")

        # 2. Pasif Araç ile Sefer Oluşturma (ID: 849 pasif olarak biliniyor)
        print("\n[2] Pasif araç (ID: 849) ile sefer oluşturma deneniyor...")
        trip_data = {
            "tarih": "2026-02-05",
            "saat": "12:00",
            "arac_id": 849,
            "sofor_id": 1,
            "guzergah_id": 13,
            "cikis_yeri": "Test",
            "varis_yeri": "Test",
            "mesafe_km": 100,
            "net_kg": 1000,
            "durum": "Bekliyor",
        }

        resp = await client.post(f"{BASE_URL}/trips/", json=trip_data, headers=headers)
        print(f"Yanıt Kodu: {resp.status_code}")
        if resp.status_code == 400:
            print(f"✅ Beklenen Hata Alındı: {resp.json()['error']['message']}")
        else:
            print(f"❌ Beklenmeyen yanıt! Beklenen: 400, Alınan: {resp.status_code}")
            print(resp.text)

        # 3. Geçersiz Araç ID ile Sefer Oluşturma
        print("\n[3] Geçersiz araç ID (ID: 9999) ile sefer oluşturma deneniyor...")
        trip_data["arac_id"] = 9999
        resp = await client.post(f"{BASE_URL}/trips/", json=trip_data, headers=headers)
        print(f"Yanıt Kodu: {resp.status_code}")
        if resp.status_code == 400:
            print(f"✅ Beklenen Hata Alındı: {resp.json()['error']['message']}")
        else:
            print("❌ Beklenmeyen yanıt!")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_inactive_logic())
