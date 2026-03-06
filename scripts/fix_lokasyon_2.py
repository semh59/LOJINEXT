import asyncio
from sqlalchemy import text
from app.database.connection import AsyncSessionLocal
import json


async def fix_data():
    async with AsyncSessionLocal() as session:
        print("🛠️ Fixing Lokasyon ID 2 manually...")
        analysis = {
            "highway": {"flat": 300.0, "up": 80.0, "down": 70.0},
            "other": {"flat": 40.0, "up": 5.0, "down": 5.0},
        }
        await session.execute(
            text("""
            UPDATE lokasyonlar SET 
                cikis_yeri = 'Ankara Lojistik Üssü', 
                varis_yeri = 'İstanbul Tuzla', 
                cikis_lat = 40.0, 
                cikis_lon = 32.5, 
                varis_lat = 40.9, 
                varis_lon = 29.3,
                mesafe_km = 500,
                api_mesafe_km = 500,
                api_sure_saat = 6.0,
                route_analysis = :details,
                otoban_mesafe_km = 450,
                sehir_ici_mesafe_km = 50
            WHERE id = 2
        """),
            {"details": json.dumps(analysis)},
        )

        await session.execute(
            text("UPDATE seferler SET mesafe_km = 500 WHERE guzergah_id = 2")
        )
        await session.commit()
    print("✅ Fixed.")


if __name__ == "__main__":
    asyncio.run(fix_data())
