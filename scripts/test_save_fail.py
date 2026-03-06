import httpx
import asyncio


async def test_save_location():
    url = "http://localhost:8000/api/v1/locations/"
    # We need a token. We can try to use a dummy or skip auth if we just want to see validation.
    # But FastAPI validates BEFORE auth dependencies in many cases, or we can see the 422 vs 401.

    payload = {
        "cikis_yeri": "Test Cikis",
        "varis_yeri": "Test Varis",
        "mesafe_km": 450.4,  # FLOAT
        "tahmini_sure_saat": 5.5,
        "zorluk": "Normal",
        "notlar": "",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")


if __name__ == "__main__":
    asyncio.run(test_save_location())
