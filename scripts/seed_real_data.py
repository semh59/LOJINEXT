import asyncio
import sys
import os
import random
from datetime import date, datetime, timedelta
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sofor, Arac, Sefer, Lokasyon, YakitAlimi

# CONSTANTS - REALISTIC DATA POOLS
DRIVERS_NAMES = [
    "Ahmet Yılmaz",
    "Mehmet Demir",
    "Mustafa Kaya",
    "Ali Çelik",
    "Hüseyin Yıldız",
    "Hasan Özdemir",
    "İbrahim Aydın",
    "İsmail Öztürk",
    "Osman Arslan",
    "Murat Doğan",
    "Yusuf Kılıç",
    "Ömer Aslan",
    "Ramazan Koç",
    "Halil Kurt",
    "Süleyman Güler",
    "Mahmut Tekin",
    "Adem Yavuz",
    "Kemal Şahin",
    "Kenan Polat",
    "Recep Yalçın",
    "Sinan Aktaş",
    "Fatih Ünal",
    "Serkan Bozkurt",
    "Metin Avcı",
    "Cengiz Taş",
    "Orhan Coşkun",
    "Sadık Erol",
    "Nihat Güneş",
    "Barış Kaplan",
    "Burak Sönmez",
    "Emre Bulut",
    "Hakan Keskin",
    "Volkan Ateş",
    "Levent Yüksel",
    "Selim Çetin",
    "Uğur Karaca",
    "Veysel Toprak",
    "Yasin Durmaz",
    "Tarık Erdoğan",
    "Cemil Korkmaz",
    "Musa Çakır",
    "Ercan Şen",
    "Gökhan Bilgin",
    "Tuncay Mutlu",
    "Mesut Turan",
    "Erkan Altun",
    "Birol Karakaş",
    "Tayfun Özkan",
    "Zafer Engin",
    "Koray Baş",
]

VEHICLE_BRANDS = [
    "Mercedes-Benz",
    "Volvo",
    "Scania",
    "MAN",
    "Ford Trucks",
    "Renault Trucks",
    "DAF",
]
VEHICLE_MODELS = {
    "Mercedes-Benz": ["Actros 1845", "Actros 1848", "Actros 1851"],
    "Volvo": ["FH 500", "FH 460", "FH16"],
    "Scania": ["R 450", "R 500", "S 500"],
    "MAN": ["TGX 18.470", "TGX 18.510"],
    "Ford Trucks": ["F-Max 500"],
    "Renault Trucks": ["T High 480", "T 460"],
    "DAF": ["XF 480", "XG 530"],
}

# City pairs with approx distances (km)
ROUTES = [
    ("İstanbul", "Ankara", 450),
    ("Ankara", "İstanbul", 450),
    ("İstanbul", "İzmir", 480),
    ("İzmir", "İstanbul", 480),
    ("İstanbul", "Bursa", 155),
    ("Bursa", "İstanbul", 155),
    ("İstanbul", "Antalya", 720),
    ("Antalya", "İstanbul", 720),
    ("İstanbul", "Adana", 940),
    ("Adana", "İstanbul", 940),
    ("Ankara", "İzmir", 590),
    ("İzmir", "Ankara", 590),
    ("Ankara", "Antalya", 480),
    ("Antalya", "Ankara", 480),
    ("İzmir", "Antalya", 460),
    ("Antalya", "İzmir", 460),
    ("Bursa", "İzmir", 330),
    ("İzmir", "Bursa", 330),
    ("İstanbul", "Edirne", 240),
    ("Edirne", "İstanbul", 240),
    ("Mersin", "Antep", 290),
    ("Antep", "Mersin", 290),
    ("Ankara", "Samsun", 410),
    ("Samsun", "Ankara", 410),
    ("İstanbul", "Trabzon", 1060),
    ("Trabzon", "İstanbul", 1060),
]


async def seed_data():
    print("🌱 Seeding High-Fidelity Data...")

    async with AsyncSessionLocal() as db:
        try:
            # 1. Create Drivers
            print("Creating 50 Drivers...")
            drivers = []
            for name in DRIVERS_NAMES:
                # Check if exists
                stmt = select(Sofor).where(Sofor.ad_soyad == name)
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    driver = Sofor(
                        ad_soyad=name,
                        telefon=f"05{random.randint(3, 5)}{random.randint(0, 9)}{random.randint(1000000, 9999999)}",
                        ise_baslama=date.today()
                        - timedelta(days=random.randint(100, 2000)),
                        ehliyet_sinifi="CE",
                        score=round(random.uniform(0.7, 1.5), 2),
                        hiz_disiplin_skoru=round(random.uniform(70, 100), 1),
                        aktif=True,
                    )
                    db.add(driver)
                    drivers.append(driver)

            await db.commit()
            print(f"✅ Added {len(drivers)} new drivers.")

            # Re-fetch all drivers
            stmt = select(Sofor)
            result = await db.execute(stmt)
            all_drivers = result.scalars().all()

            # 2. Create Vehicles
            print("Creating 30 Vehicles...")
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            vehicles = []

            for i in range(30):
                brand = random.choice(VEHICLE_BRANDS)
                model = random.choice(VEHICLE_MODELS[brand])
                plaka = f"34 {random.choice(chars)}{random.choice(chars)} {random.randint(100, 9999)}"

                stmt = select(Arac).where(Arac.plaka == plaka)
                result = await db.execute(stmt)
                if not result.scalar_one_or_none():
                    vehicle = Arac(
                        plaka=plaka,
                        marka=brand,
                        model=model,
                        yil=random.randint(2018, 2024),
                        tank_kapasitesi=random.choice([600, 800, 1000]),
                        hedef_tuketim=random.uniform(28.0, 34.0),
                        aktif=True,
                    )
                    db.add(vehicle)
                    vehicles.append(vehicle)

            await db.commit()
            print(f"✅ Added {len(vehicles)} new vehicles.")

            # Re-fetch all vehicles
            stmt = select(Arac)
            result = await db.execute(stmt)
            all_vehicles = result.scalars().all()

            # 3. Create Routes & Locations
            print("Creating Routes...")
            all_routes = []

            for origin, dest, dist in ROUTES:
                # Create Lokasyon if needed?
                # For simplified seeding, we just create Guzergah directly if model permits,
                # but Sefer links to Lokasyon via guzergah_id (which is actually Lokasyon table foreign key in schema???)
                # Wait, schema check: Sefer.guzergah_id -> Lokasyon.id.
                # Guzergah model is separate.
                # Let's create Locations first

                # Check location pair
                stmt = select(Lokasyon).where(
                    Lokasyon.cikis_yeri == origin, Lokasyon.varis_yeri == dest
                )
                result = await db.execute(stmt)
                loc = result.scalar_one_or_none()

                if not loc:
                    loc = Lokasyon(
                        cikis_yeri=origin,
                        varis_yeri=dest,
                        mesafe_km=dist,
                        tahmini_sure_saat=dist / 70.0,  # Avg 70km/h
                        flat_distance_km=dist * 0.9,
                        tahmini_yakit_lt=(dist / 100.0) * 32.0,
                        zorluk=random.choice(["Kolay", "Normal", "Zor"]),
                    )
                    db.add(loc)
                    await db.flush()  # get ID

                all_routes.append(loc)

            await db.commit()
            print(f"✅ Configured {len(all_routes)} route pairs.")

            # 4. Generate Trips & Fuel Records (The Anatolian Logistics Flow)
            print("Generatng 500+ Trips & Fuel Records...")

            if not all_drivers or not all_vehicles or not all_routes:
                print("❌ Missing base data (drivers/vehicles/routes).")
                return

            trips_created = 0
            fuel_records_created = 0

            # TRACKING STATE
            # vehicle_id -> { 'current_fuel': float, 'km_counter': int, 'last_loc': str }
            vehicle_states = {}
            for v in all_vehicles:
                vehicle_states[v.id] = {
                    "current_fuel": v.tank_kapasitesi
                    * random.uniform(0.4, 0.6),  # Start 40-60%
                    "km_counter": random.randint(50000, 450000),
                    "last_loc": "İstanbul",  # Assume all start at main hub
                }

            curr_date = date.today() - timedelta(days=90)  # Start 3 months ago
            end_date = date.today()

            # Fuel Prices History (approx)
            FUEL_PRICE_BASE = 42.50

            # Simulation Loop
            day_cursor = curr_date
            while day_cursor <= end_date:
                daily_trips_count = random.randint(5, 12)  # Busy fleet

                # Update Fuel Price slightly
                daily_fuel_price = FUEL_PRICE_BASE + random.uniform(-2.0, 3.0)

                todays_vehicles = random.sample(
                    all_vehicles, k=min(len(all_vehicles), daily_trips_count)
                )

                for veh in todays_vehicles:
                    state = vehicle_states[veh.id]

                    # 1. PLAN TRIP
                    # Find route starting from last_loc
                    possible_routes = [
                        r for r in all_routes if r.cikis_yeri == state["last_loc"]
                    ]
                    if not possible_routes:
                        # Deadhead to random hub (skip recording empty move for simplicity, just teleport)
                        route = random.choice(all_routes)
                    else:
                        route = random.choice(possible_routes)

                    # Calculate Expected Consumption
                    # PHYSICS-BASED CONSUMPTION CALCULATION
                    base_consumption_100km = veh.hedef_tuketim

                    drv = random.choice(all_drivers)  # Assign driver

                    tonnage = random.randint(0, 25)
                    load_impact = tonnage * 0.5

                    # Driver Impact
                    driver_factor = 1.0 + ((1.0 - drv.score) * 0.2)

                    # Route Difficulty
                    diff_factor = 1.0
                    if route.zorluk == "Zor":
                        diff_factor = 1.25
                    elif route.zorluk == "Normal":
                        diff_factor = 1.10
                    elif route.zorluk == "Kolay":
                        diff_factor = 0.95

                    # Final L/100km & Liters
                    final_consumption_100km = (
                        (base_consumption_100km + load_impact)
                        * driver_factor
                        * diff_factor
                    )
                    noise = random.uniform(0.95, 1.05)
                    final_consumption_100km *= noise

                    estimated_needed_fuel = (
                        route.mesafe_km / 100.0
                    ) * final_consumption_100km

                    # 2. CHECK FUEL & REFUEL IF NEEDED
                    # Threashold: 20% or if not enough for trip
                    tank_cap = veh.tank_kapasitesi
                    low_fuel_threshold = tank_cap * 0.20

                    if state["current_fuel"] < low_fuel_threshold or state[
                        "current_fuel"
                    ] < (estimated_needed_fuel * 1.2):
                        # REFUEL EVENT
                        # Target: 85-95% (Never 100%)
                        target_level = tank_cap * random.uniform(0.85, 0.95)
                        refuel_liter = target_level - state["current_fuel"]

                        if refuel_liter > 10:  # Minimum refuel
                            receipt = YakitAlimi(
                                tarih=day_cursor,
                                arac_id=veh.id,
                                istasyon=random.choice(
                                    ["Shell", "Opet", "BP", "Petrol Ofisi", "Total"]
                                ),
                                fiyat_tl=round(daily_fuel_price, 2),
                                litre=round(refuel_liter, 2),
                                toplam_tutar=round(refuel_liter * daily_fuel_price, 2),
                                km_sayac=int(state["km_counter"]),
                                fis_no=f"FIS{random.randint(10000, 99999)}",
                                depo_durumu="Dolu"
                                if target_level > (tank_cap * 0.9)
                                else "Kısmi",
                                durum="Onaylandi",
                                aktif=True,
                            )
                            db.add(receipt)
                            fuel_records_created += 1
                            state["current_fuel"] += refuel_liter
                            # Flush to ensure ID order roughly matches
                            await db.flush()

                    # 3. EXECUTE TRIP
                    # Anomaly Injection
                    is_anomaly = False
                    anomaly_type = None
                    actual_consumed = estimated_needed_fuel

                    if random.randint(1, 50) == 1:
                        if random.choice([True, False]):
                            actual_consumed *= 1.4  # Theft/Leak
                            is_anomaly = True
                            anomaly_type = "High Consumption"
                        else:
                            actual_consumed *= 0.7  # Coasting
                            is_anomaly = True
                            anomaly_type = "Low Consumption"

                    # Update Vehicle State
                    state["current_fuel"] -= actual_consumed
                    state["km_counter"] += route.mesafe_km
                    state["last_loc"] = route.varis_yeri  # Move vehicle

                    # Create Trip Record
                    trip = Sefer(
                        tarih=day_cursor,
                        saat=f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}",
                        guzergah_id=route.id,
                        arac_id=veh.id,
                        sofor_id=drv.id,
                        cikis_yeri=route.cikis_yeri,
                        varis_yeri=route.varis_yeri,
                        mesafe_km=route.mesafe_km,
                        bos_agirlik_kg=14500,
                        dolu_agirlik_kg=14500 + (tonnage * 1000),
                        net_kg=tonnage * 1000,
                        ton=float(tonnage),
                        durum="Tamam",
                        bos_sefer=(tonnage == 0),
                        dagitilan_yakit=round(actual_consumed, 2),
                        tuketim=round(final_consumption_100km, 2),  # L/100km
                        tahmini_tuketim=round(final_consumption_100km / noise, 2),
                        notlar="Simulated"
                        + (f" [ANOMALY: {anomaly_type}]" if is_anomaly else ""),
                    )
                    db.add(trip)
                    trips_created += 1

                day_cursor += timedelta(days=1)

            await db.commit()
            print(f"✅ Generated {trips_created} trips.")
            print(f"✅ Generated {fuel_records_created} fuel records.")
            print("🚀 Real Data Seeding Complete!")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            import traceback

            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(seed_data())
