import os
import asyncio
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import connections
from app.database.connection import AsyncSessionLocal
from app.database.models import Lokasyon, Sefer, Arac, Sofor
from app.infrastructure.routing.openroute_client import OpenRouteClient

load_dotenv()


async def hard_reset_and_reseed():
    print("🚀 ULTIMATE Recovery Operation Started...")

    async with AsyncSessionLocal() as session:
        print("🗑️ Clearing existing data...")
        await session.execute(text("TRUNCATE TABLE seferler RESTART IDENTITY CASCADE"))
        await session.execute(
            text("TRUNCATE TABLE lokasyonlar RESTART IDENTITY CASCADE")
        )
        await session.commit()

    # Reliably mappable coordinates
    routes_raw = [
        {
            "cikis_yeri": "Ankara (Merkez)",
            "varis_yeri": "İzmir (Konak)",
            "cikis_lat": 39.9208,
            "cikis_lon": 32.8541,
            "varis_lat": 38.4189,
            "varis_lon": 27.1287,
            "zorluk": "Orta",
            "notlar": "Batı sevkiyat hattı.",
        },
        {
            "cikis_yeri": "Adana (Merkez)",
            "varis_yeri": "İstanbul (Beyoğlu)",
            "cikis_lat": 36.9914,
            "cikis_lon": 35.3308,
            "varis_lat": 41.0082,
            "varis_lon": 28.9784,
            "zorluk": "Normal",
            "notlar": "Kuzey-Güney koridoru.",
        },
    ]

    client = OpenRouteClient()
    created_locations = []

    async with AsyncSessionLocal() as session:
        for r in routes_raw:
            print(f"📍 Adding: {r['cikis_yeri']} -> {r['varis_yeri']}...")
            loc = Lokasyon(
                cikis_yeri=r["cikis_yeri"],
                varis_yeri=r["varis_yeri"],
                cikis_lat=r["cikis_lat"],
                cikis_lon=r["cikis_lon"],
                varis_lat=r["varis_lat"],
                varis_lon=r["varis_lon"],
                zorluk=r["zorluk"],
                mesafe_km=0,
                aktif=True,
                notlar=r["notlar"],
            )
            session.add(loc)
            await session.commit()
            await session.refresh(loc)

            # Analyze immediately
            print(f"🔍 Analyzing {loc.id}...")
            result = await asyncio.to_thread(client.update_route_distance, loc.id)

            # Refresh to get updated mesafe_km
            await session.refresh(loc)
            created_locations.append(loc)

    # Trips Seeding
    print("🚛 Generating trip records...")
    async with AsyncSessionLocal() as session:
        # Get valid dependencies
        res = await session.execute(
            text("SELECT id FROM araclar WHERE aktif = true LIMIT 5")
        )
        v_ids = [row[0] for row in res.all()]

        res = await session.execute(
            text("SELECT id FROM soforler WHERE aktif = true LIMIT 5")
        )
        s_ids = [row[0] for row in res.all()]

        if not v_ids or not s_ids:
            print("❌ Vehicles or Drivers missing! Cannot seed trips.")
            return

        start_date = datetime.now() - timedelta(days=90)

        for i in range(120):
            loc = random.choice(created_locations)
            vid = random.choice(v_ids)
            sid = random.choice(s_ids)
            ton = random.uniform(5, 25)

            # Realistic consumption
            base = 25.0 if "İzmir" in loc.varis_yeri else 22.0
            actual = base + (ton * 0.45) + random.uniform(-1, 1)

            sefer = Sefer(
                tarih=(start_date + timedelta(hours=i * 6)).date(),
                arac_id=vid,
                sofor_id=sid,
                guzergah_id=loc.id,
                cikis_yeri=loc.cikis_yeri,
                varis_yeri=loc.varis_yeri,
                mesafe_km=loc.mesafe_km or 500,
                ton=ton,
                bos_agirlik_kg=15000,
                dolu_agirlik_kg=15000 + int(ton * 1000),
                net_kg=int(ton * 1000),
                tuketim=actual,
                tahmini_tuketim=actual * random.uniform(0.95, 1.05),
                durum="Tamam",
            )
            session.add(sefer)

        await session.commit()

    print("✅ ULTIMATE RECOVERY COMPLETE.")


if __name__ == "__main__":
    asyncio.run(hard_reset_and_reseed())
