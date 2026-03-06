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
    print("🚀 Starting Hard Reset & Reseed Operation...")

    # 1. Hard Delete
    async with AsyncSessionLocal() as session:
        print("🗑️ Deleting all Sefer and Lokasyon records...")
        await session.execute(text("TRUNCATE TABLE seferler RESTART IDENTITY CASCADE"))
        await session.execute(
            text("TRUNCATE TABLE lokasyonlar RESTART IDENTITY CASCADE")
        )
        await session.commit()

    # 2. Add Critical Routes
    routes = [
        {
            "cikis_yeri": "Ankara Merkez",
            "varis_yeri": "İzmir Liman",
            "cikis_lat": 39.9334,
            "cikis_lon": 32.8597,
            "varis_lat": 38.4435,
            "varis_lon": 27.1444,
            "zorluk": "Orta",
            "notlar": "Ana sevkiyat hattı.",
        },
        {
            "cikis_yeri": "Adana Nakliyeciler",
            "varis_yeri": "İstanbul Ambarlı",
            "cikis_lat": 36.9914,
            "cikis_lon": 35.3308,
            "varis_lat": 40.9691,
            "varis_lon": 28.6944,
            "zorluk": "Normal",
            "notlar": "Güney hattı.",
        },
    ]

    client = OpenRouteClient()
    created_locations = []

    async with AsyncSessionLocal() as session:
        for r in routes:
            print(f"📍 Creating route: {r['cikis_yeri']} -> {r['varis_yeri']}...")
            loc = Lokasyon(
                cikis_yeri=r["cikis_yeri"],
                varis_yeri=r["varis_yeri"],
                cikis_lat=r["cikis_lat"],
                cikis_lon=r["cikis_lon"],
                varis_lat=r["varis_lat"],
                varis_lon=r["varis_lon"],
                zorluk=r["zorluk"],
                mesafe_km=0,
                notlar=r["notlar"],
            )
            session.add(loc)
            await session.commit()
            await session.refresh(loc)
            created_locations.append(loc)

            # Trigger analysis
            print(f"🔍 Analyzing route {loc.id}...")
            await asyncio.to_thread(client.update_route_distance, loc.id)

    # 3. Seed Trips for Retraining
    print("🚛 Seeding 120 trips for models...")

    async with AsyncSessionLocal() as session:
        # Get vehicles - Ensure we use a simple SELECT
        result = await session.execute(
            text("SELECT id FROM araclar WHERE aktif = true LIMIT 10")
        )
        vehicle_ids = [row[0] for row in result.all()]
        print(f"DEBUG: Found {len(vehicle_ids)} vehicle IDs: {vehicle_ids}")

        if not vehicle_ids:
            print("⚠️ No vehicles found. Creating a dummy vehicle...")
            dummy = Arac(
                plaka="06-LJN-001",
                marka="Mercedes",
                model="Actros",
                tank_kapasitesi=600,
                hedef_tuketim=31.5,
                aktif=True,
            )
            session.add(dummy)
            await session.commit()
            await session.refresh(dummy)
            vehicle_ids = [dummy.id]

        # Get locations
        result = await session.execute(text("SELECT id, mesafe_km FROM lokasyonlar"))
        loc_rows = result.all()
        loc_data = [(row[0], float(row[1] or 0)) for row in loc_rows]
        print(f"DEBUG: Found {len(loc_data)} locations: {loc_data}")

        if not loc_data:
            print("❌ No locations found to seed trips!")
            return

        base_date = datetime.now() - timedelta(days=60)

        for i in range(120):
            loc_id, base_dist = random.choice(loc_data)
            v_id = random.choice(vehicle_ids)

            ton = random.uniform(5, 25)
            # Consumption logic: base 22L + random noise
            is_ankara = loc_id == created_locations[0].id
            base_cons = 25.0 if is_ankara else 22.0
            consumption = base_cons + (ton * 0.45) + random.uniform(-1, 1)

            sefer = Sefer(
                arac_id=v_id,
                guzergah_id=loc_id,
                tarih=base_date + timedelta(hours=i * 4),
                ton=ton,
                mesafe_km=base_dist,
                tuketim=consumption,
                tahmini_tuketim=consumption * random.uniform(0.95, 1.05),
            )
            session.add(sefer)

        print(f"DEBUG: Committing 120 trips...")
        try:
            await session.commit()
            print("✅ Trips committed successfully.")
        except Exception as e:
            print(f"❌ Failed to commit trips: {e}")
            await session.rollback()

    print("\n🎉 HARD RESET & RESEED COMPLETE!")


if __name__ == "__main__":
    asyncio.run(hard_reset_and_reseed())
