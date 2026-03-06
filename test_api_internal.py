"""
A standalone script to execute backend service directly using FastAPI test client.
This bypasses network ports to prove if the code itself works.
"""

import sys
import os
import asyncio
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.api.deps import get_current_active_admin, get_current_user
from app.database.models import Kullanici

client = TestClient(app)

# Mock user for testing
test_admin = Kullanici(
    id=1,
    email="test@admin.com",
    aktif=True,
    rol_id=1,
    ad_soyad="mock",
    sifre_hash="mock",
)

app.dependency_overrides[get_current_user] = lambda: test_admin
app.dependency_overrides[get_current_active_admin] = lambda: test_admin


def test_get_trailers():
    print("Testing GET /api/v1/trailers/...")
    response = client.get("/api/v1/trailers/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_create_trailer():
    print("Testing POST /api/v1/trailers/...")
    payload = {
        "plaka": "34 TES 001",
        "marka": "Test Brand",
        "tipi": "Standart",
        "yil": 2024,
        "bos_agirlik_kg": 6000.0,
        "hedef_tuketim": 0,
        "maks_yuk_kapasitesi_kg": 24000,
        "lastik_sayisi": 6,
        "aktif": True,
    }
    response = client.post("/api/v1/trailers/", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    print("--- Starting FastAPI Internal API Test ---")
    test_get_trailers()
    print("-" * 20)
    test_create_trailer()
    print("--- Test Complete ---")
