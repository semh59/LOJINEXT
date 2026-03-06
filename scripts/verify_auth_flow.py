import asyncio
import sys
import os
from unittest.mock import MagicMock


# --- DEFENSIVE MOCKING ---
class MockModule(MagicMock):
    def __getattr__(self, name):
        return MagicMock()


missing_deps = [
    "sentry_sdk",
    "prometheus_fastapi_instrumentator",
    "groq",
    "openai",
    "sentence_transformers",
    "faiss",
    "reportlab",
    "matplotlib",
    "openpyxl",
    "xlsxwriter",
    "openrouteservice",
]

for dep in missing_deps:
    if dep not in sys.modules:
        sys.modules[dep] = MockModule()

# Add project root to path
sys.path.append(os.path.abspath(os.getcwd()))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


async def test_auth():
    print("--- LOJINEXT FINAL ULTIMATE DEEP TEST ---")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login
        print("\n[STEP 1] Login with Super Admin")
        login_data = {
            "username": settings.SUPER_ADMIN_USERNAME,
            "password": (
                settings.SUPER_ADMIN_PASSWORD.get_secret_value()
                if settings.SUPER_ADMIN_PASSWORD
                else "!23efe25ali!"
            ),
        }
        response = await ac.post("/api/v1/auth/token", data=login_data)

        if response.status_code == 200:
            print("[OK] Login successful")
            tokens = response.json()
            access_token = tokens["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
        else:
            print(f"[FAIL] Login failed: {response.status_code} - {response.text}")
            return

        # 2. Get User Info
        print("\n[STEP 2] Get Current User (/api/v1/auth/me)")
        response = await ac.get("/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            print(f"[OK] Schema validation passed. User: {response.json()['email']}")
        else:
            print(
                f"[FAIL] User info check failed: {response.status_code} - {response.text}"
            )

        # 3. Update Config (PUT)
        print("\n[STEP 3] Update Config Parameter")
        update_data = {"value": "9.81", "reason": "Verifying Elite Audit System"}
        response = await ac.put(
            "/api/v1/admin/config/physics.gravity", json=update_data, headers=headers
        )

        if response.status_code == 200:
            print("[OK] Config update successful")
            updated = response.json()
            print(f"New Value: {updated['deger']}")
        else:
            print(
                f"[FAIL] Config update failed: {response.status_code} - {response.text}"
            )

        # 4. Verify Audit Log
        print("\n[STEP 4] Verify Audit Log entry")
        from sqlalchemy import text
        from app.database.connection import engine

        async with engine.connect() as conn:
            # Use correct column names: aksiyon_tipi, aciklama
            result = await conn.execute(
                text(
                    "SELECT aksiyon_tipi, aciklama FROM admin_audit_log ORDER BY id DESC LIMIT 1"
                )
            )
            row = result.fetchone()
            if row and "CONFIG_UPDATE" in row[0]:
                print(f"[OK] Audit log entry found: {row[0]}")
                print(f"Description: {row[1]}")
            else:
                print(f"[FAIL] Audit log entry not found or mismatch: {row}")


if __name__ == "__main__":
    os.environ["ENVIRONMENT"] = "test"
    try:
        asyncio.run(test_auth())
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Test script crashed: {e}")
        import traceback

        traceback.print_exc()
