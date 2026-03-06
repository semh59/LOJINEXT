import httpx
from datetime import datetime


async def test_route_info():
    """/route-info endpoint'ini test eder"""
    base_url = "http://localhost:8000/api/v1/locations/route-info"

    # Test koordinatları (Ankara -> İstanbul)
    params = {
        "cikis_lat": 39.9334,
        "cikis_lon": 32.8597,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
    }

    print(f"[{datetime.now()}] Testing route-info endpoint...")
    print(f"Coordinates: {params}")

    async with httpx.AsyncClient() as client:
        try:
            # Not: Auth gerekebilir, gerçek bir testte token eklenmeli
            # Ancak biz burada endpoint'in varlığını ve temel dönütünü simüle ediyoruz
            response = await client.get(base_url, params=params)

            if response.status_code == 401:
                print("Result: 401 Unauthorized (Expected if no token provided)")
                print("Endpoint exists and AUTH is working.")
            elif response.status_code == 200:
                print("Result: 200 OK")
                data = response.json()
                print(f"Distance: {data.get('distance_km')} km")
                print(f"Ascent: {data.get('ascent_m')} m")
            else:
                print(f"Result: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Bu script manuel trigger'lanabilir veya backend çalışırken denenebilir.
    # Şimdilik servis katmanını test eden bir birim testi daha güvenlidir.
    pass
