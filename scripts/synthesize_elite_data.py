import asyncio
import random
import sys
import os
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict
from decimal import Decimal

# Project Root
sys.path.append(os.getcwd())

from sqlalchemy import delete, text, select
from app.database.connection import engine, AsyncSessionLocal
from app.database.models import (
    Base,
    Arac,
    Sofor,
    Sefer,
    YakitAlimi,
    Lokasyon,
    YakitPeriyodu,
    YakitFormul,
    Anomaly,
    Alert,
    RoutePath,
    ModelVersion,
)
from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    RouteConditions,
    VehicleSpecs,
)
from app.infrastructure.logging.logger import setup_logging

logger = setup_logging("synthesis")

# --- SETTINGS ---
VEHICLE_COUNT = 10
DRIVER_COUNT = 15
TRIPS_PER_VEHICLE = 50
START_DATE = datetime(2025, 12, 1)

# ARCHETYPES
VEHICLE_ARCHETYPES = [
    {"marka": "Mercedes-Benz", "model": "Actros 1845", "yil": 2024, "tank": 650},
    {"marka": "Scania", "model": "R450", "yil": 2023, "tank": 700},
    {"marka": "Volvo", "model": "FH13 500", "yil": 2025, "tank": 750},
    {"marka": "MAN", "model": "TGX 18.440", "yil": 2022, "tank": 600},
    {"marka": "DAF", "model": "XF 480", "yil": 2023, "tank": 650},
]

# Physical Archetypes for Master Routes
ROUTE_ARCHETYPES = [
    {
        "cikis": "İstanbul",
        "varis": "Erzurum",
        "mesafe": 1230,
        "ascent": 2200,
        "descent": 1500,
        "zorluk": "Zor",
        "sensitivity": 1.2,
        "road_analysis": {
            "motorway": {"flat": 800, "up": 100, "down": 50},
            "trunk": {"flat": 200, "up": 50, "down": 30},
        },
    },
    {
        "cikis": "Bursa",
        "varis": "İzmir",
        "mesafe": 345,
        "ascent": 300,
        "descent": 300,
        "zorluk": "Kolay",
        "sensitivity": 0.7,
        "road_analysis": {"motorway": {"flat": 300, "up": 20, "down": 25}},
    },
    {
        "cikis": "Ankara",
        "varis": "Konya",
        "mesafe": 260,
        "ascent": 200,
        "descent": 150,
        "zorluk": "Kolay",
        "sensitivity": 0.8,
        "road_analysis": {"motorway": {"flat": 250, "up": 5, "down": 5}},
    },
    {
        "cikis": "Antalya",
        "varis": "Mersin",
        "mesafe": 480,
        "ascent": 1200,
        "descent": 1200,
        "zorluk": "Zor",
        "sensitivity": 1.1,
        "road_analysis": {"trunk": {"flat": 300, "up": 90, "down": 90}},
    },
    {
        "cikis": "Lüleburgaz",
        "varis": "İstanbul",
        "mesafe": 160,
        "ascent": 150,
        "descent": 150,
        "zorluk": "Normal",
        "sensitivity": 1.0,
        "road_analysis": {"motorway": {"flat": 140, "up": 10, "down": 10}},
    },
]


async def clear_database():
    """Tüm verileri temizle (Sıralı)"""
    logger.info("Cleaning database...")
    async with AsyncSessionLocal() as session:
        # Dependency order: Formula/Anomaly/Periyot -> Yakit/Sefer -> Arac/Sofor
        await session.execute(delete(YakitFormul))
        await session.execute(delete(Anomaly))
        await session.execute(delete(Alert))
        await session.execute(delete(RoutePath))
        await session.execute(delete(ModelVersion))
        await session.execute(delete(YakitPeriyodu))
        await session.execute(delete(YakitAlimi))
        await session.execute(delete(Sefer))
        await session.execute(delete(Lokasyon))  # NEW: Clear routes too
        await session.execute(delete(Arac))
        await session.execute(delete(Sofor))
        await session.commit()
    logger.info("Database cleaned.")


async def synthesize_master_data():
    """Araç, Şoför ve Master Rotaları oluştur"""
    logger.info("Synthesizing Master Data...")
    async with AsyncSessionLocal() as session:
        # 1. Routes (Lokasyon)
        master_routes = []
        for r_arch in ROUTE_ARCHETYPES:
            lok = Lokasyon(
                cikis_yeri=r_arch["cikis"],
                varis_yeri=r_arch["varis"],
                mesafe_km=float(r_arch["mesafe"]),
                zorluk=r_arch["zorluk"],
                ascent_m=float(r_arch["ascent"]),
                descent_m=float(r_arch["descent"]),
                route_analysis=r_arch["road_analysis"],
                aktif=True,
            )
            session.add(lok)
            master_routes.append({"arch": r_arch, "entity": lok})

        # 2. Drivers
        drivers = []
        for i in range(DRIVER_COUNT):
            score = round(random.uniform(0.92, 1.15), 3)
            d = Sofor(ad_soyad=f"Elite Driver {chr(65 + i)}", score=score, aktif=True)
            session.add(d)
            drivers.append(d)

        # 3. Vehicles
        vehicles = []
        for i in range(VEHICLE_COUNT):
            arch = random.choice(VEHICLE_ARCHETYPES)
            v = Arac(
                plaka=f"{34 if i % 2 == 0 else 6} LOJ {100 + i}",
                marka=arch["marka"],
                model=arch["model"],
                yil=arch["yil"],
                tank_kapasitesi=arch["tank"],
                hedef_tuketim=32.0,
                bos_agirlik_kg=14500.0,
                hava_direnc_katsayisi=0.65,
                on_kesit_alani_m2=8.2,
                motor_verimliligi=0.40,
                aktif=True,
            )
            session.add(v)
            vehicles.append(v)

        await session.commit()
        # Refresh to get IDs
        for r in master_routes:
            await session.refresh(r["entity"])
        for d in drivers:
            await session.refresh(d)
        for v in vehicles:
            await session.refresh(v)

        return drivers, vehicles, master_routes


async def synthesize_missions(drivers, vehicles, master_routes):
    """Seferleri ve Yakıt Alımlarını oluştur"""
    logger.info("Synthesizing missions...")
    physics = PhysicsBasedFuelPredictor()

    async with AsyncSessionLocal() as session:
        for v in vehicles:
            current_km = 100000
            current_date = START_DATE
            fuel_in_tank = v.tank_kapasitesi * 0.8

            # Initial Fueling
            f_init = YakitAlimi(
                arac_id=v.id,
                tarih=current_date.date(),
                istasyon="Hq-Storage",
                litre=Decimal(str(v.tank_kapasitesi * 0.8)),
                km_sayac=current_km,
                depo_durumu="Dolu",
                durum="Onaylandi",
            )
            session.add(f_init)

            for tri_idx in range(TRIPS_PER_VEHICLE):
                d = random.choice(drivers)
                m_route = random.choice(master_routes)
                arch = m_route["arch"]
                lok = m_route["entity"]

                # Jitter for variety
                mesafe = arch["mesafe"] * random.uniform(0.98, 1.02)
                load = random.uniform(5, 26)
                ascent = arch["ascent"] * random.uniform(0.95, 1.05)
                descent = arch["descent"] * random.uniform(0.95, 1.05)

                route_data = RouteConditions(
                    distance_km=float(mesafe),
                    load_ton=float(load),
                    ascent_m=float(ascent),
                    descent_m=float(descent),
                )

                prediction = physics.predict(route_data)
                base_l_100 = prediction.consumption_l_100km

                # Factors
                driver_impact = 1 + (d.score - 1) * arch.get("sensitivity", 1.0)
                vehicle_bias = 1.03 if (v.id % 5 == 0) else 1.0  # Bias for 2 vehicles
                noise = np.random.normal(0, 0.015)  # Tighter noise for elite data

                actual_l_100 = base_l_100 * driver_impact * vehicle_bias * (1 + noise)
                consumed_liters = (actual_l_100 * mesafe) / 100

                current_km += int(mesafe)
                current_date += timedelta(hours=random.randint(24, 72))

                s = Sefer(
                    tarih=current_date.date(),
                    arac_id=v.id,
                    sofor_id=d.id,
                    guzergah_id=lok.id,
                    cikis_yeri=lok.cikis_yeri,
                    varis_yeri=lok.varis_yeri,
                    mesafe_km=float(mesafe),
                    baslangic_km=current_km - int(mesafe),
                    bitis_km=current_km,
                    ton=float(load),
                    tuketim=round(actual_l_100, 2),
                    ascent_m=float(ascent),
                    descent_m=float(descent),
                    dagitilan_yakit=Decimal(str(round(consumed_liters, 2))),
                    durum="Tamam",
                    is_real=False,
                    rota_detay=lok.route_analysis,
                )
                session.add(s)

                fuel_in_tank -= round(consumed_liters, 2)

                if fuel_in_tank < 100:
                    refill = v.tank_kapasitesi - fuel_in_tank
                    f = YakitAlimi(
                        arac_id=v.id,
                        tarih=current_date.date(),
                        istasyon=f"Shell-En-Route-{random.randint(1, 10)}",
                        litre=Decimal(str(round(refill, 2))),
                        km_sayac=current_km,
                        depo_durumu="Dolu",
                        durum="Onaylandi",
                    )
                    session.add(f)
                    fuel_in_tank = v.tank_kapasitesi

            await session.commit()
            logger.info(f"Vehicle {v.plaka} synchronized.")


async def main():
    await clear_database()
    drivers, vehicles, routes = await synthesize_master_data()
    await synthesize_missions(drivers, vehicles, routes)
    logger.info("ELITE DATA HUB (V2) SYNTHESIS COMPLETE.")


if __name__ == "__main__":
    asyncio.run(main())
