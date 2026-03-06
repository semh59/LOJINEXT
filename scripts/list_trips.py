import asyncio
import os
import sys
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal


async def list_trips():
    async with AsyncSessionLocal() as db:
        print("\n--- LAST 5 TRIPS ---")
        try:
            query = "SELECT id, tarih, sefer_no, cikis_yeri, varis_yeri FROM seferler ORDER BY id DESC LIMIT 5"
            result = await db.execute(text(query))
            trips = result.fetchall()
            for t in trips:
                print(
                    f"ID: {t[0]} | Tarih: {t[1]} | Sefer No: {t[2]} | Route: {t[3]}->{t[4]}"
                )
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(list_trips())
