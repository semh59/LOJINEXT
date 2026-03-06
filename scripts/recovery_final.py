import os
import asyncio
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import connections
from app.database.connection import AsyncSessionLocal
from app.database.models import Lokasyon, Sefer, Arac
from app.infrastructure.routing.openroute_client import OpenRouteClient

load_dotenv()


async def hard_reset_and_reseed():
    print("🚀 Final Recovery Operation Started...")

    async with AsyncSessionLocal() as session:
        print("🗑️ Clearing existing data...")
        await session.execute(text("TRUNCATE TABLE seferler RESTART IDENTITY CASCADE"))
        await session.execute(
            text("TRUNCATE TABLE lokasyonlar RESTART IDENTITY CASCADE")
        )
        await session.commit()

    # Reliably mappable coordinates
    routes = [
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
            "cikis_yeri": "Adana (Seyhan)",
            "varis_yeri": "İstanbul (Beyoğlu)",
            "cikis_lat": 36.9914,
            "cikis_lon": 35.3308,
            "varis_lat": 41.0285,
            "varis_lon": 28.9744,
            "zorluk": "Normal",
            "notlar": "Kuzey-Güney koridoru.",
        },
    ]

    client = OpenRouteClient()
    loc_ids = []

    async with AsyncSessionLocal() as session:
        for r in routes:
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
            loc_ids.append(loc.id)

            # Analyze immediately
            print(f"🔍 Analyzing {loc.id}...")
            # We use asyncio.to_thread because update_route_distance is sync and handles its own session
            result = await asyncio.to_thread(client.update_route_distance, loc.id)
            if not result:
                print(f"⚠️ API failed for {loc.id}, using mock fallback.")
                # Mock fallback if API fails
                await session.execute(
                    text("""
                    UPDATE lokasyonlar SET 
                        mesafe_km = 600, 
                        api_mesafe_km = 600, 
                        api_sure_saat = 7.5,
                        route_analysis = '{"highway": {"flat": 400, "up": 100, "down": 100}, "other": {"flat": 50, "up": 25, "down": 25}}'
                    WHERE id = :id
                """),
                    {"id": loc.id},
                )
                await session.commit()

    # Trips Seeding
    print("🚛 Generating trip records...")
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id FROM araclar WHERE aktif = true"))
        v_ids = [row[0] for row in res.all()]
        if not v_ids:
            v_ids = [1]  # Fallback

        res = await session.execute(text("SELECT id, mesafe_km FROM lokasyonlar"))
        loc_data = res.all()  # list of (id, mesafe)

        start_date = datetime.now() - timedelta(days=90)

        for i in range(150):
            l_id, dist = random.choice(loc_data)
            vid = random.choice(v_ids)
            ton = random.uniform(2, 28)

            # Realistic consumption (avg 32L/100km + load factor)
            base = 24.0 if l_id == loc_ids[0] else 22.0
            actual = base + (ton * 0.45) + random.uniform(-1.5, 1.5)

            sefer = Sefer(
                arac_id=vid,
                guzergah_id=l_id,
                tarih=start_date + timedelta(hours=i * 6),
                ton=ton,
                mesafe_km=dist or 500,
                tuketim=actual,
                tahmini_tuketim=actual * random.uniform(0.9, 1.1),
            )
            session.add(sefer)

        await session.commit()

    print("✅ RECOVERY COMPLETE.")


if __name__ == "__main__":
    asyncio.run(hard_reset_and_reseed())
