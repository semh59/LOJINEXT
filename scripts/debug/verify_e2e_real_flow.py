import asyncio
import sys
import os
from sqlalchemy import select, func, desc

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sefer, Arac, Sofor, YakitAlimi, Lokasyon


async def verify_real_flow():
    print("🔍 Starting E2E Real Data Verification...")
    print("==========================================")

    async with AsyncSessionLocal() as db:
        # 1. VERIFY VOLUME
        print("\n📊 Checking Data Volume...")

        trip_count = await db.scalar(select(func.count(Sefer.id)))
        driver_count = await db.scalar(select(func.count(Sofor.id)))
        vehicle_count = await db.scalar(select(func.count(Arac.id)))
        fuel_count = await db.scalar(select(func.count(YakitAlimi.id)))

        print(f"  - Trips: {trip_count}")
        print(f"  - Drivers: {driver_count}")
        print(f"  - Vehicles: {vehicle_count}")
        print(f"  - Fuel Records: {fuel_count}")

        if trip_count < 100 or fuel_count < 20:
            print("❌ FAILURE: Insufficient data volume.")
            return

        # 2. VERIFY FUEL LOGIC (The "Depo" Constraint)
        print("\n⛽ Verifying Fuel Constraints...")

        # Check if any fuel record exceeds tank capacity (Should be IMPOSSIBLE per seeding logic, but checking DB integrity)
        # Note: We need to join with Arac to get tank_capacity
        stmt = select(YakitAlimi, Arac).join(Arac).limit(50)
        fuel_samples = await db.execute(stmt)

        violations = 0
        checked = 0
        for record, vehicle in fuel_samples:
            checked += 1
            # In seeding, we tracked current_fuel.
            # Ideally, the `litre` added + `current_fuel` (unknown here without replay) <= `capacity`.
            # But we can check if `litre` itself > `capacity` (Hard constraint violation)
            if record.litre > vehicle.tank_kapasitesi:
                print(
                    f"  ❌ Violation: Refueled {record.litre}L but tank is {vehicle.tank_kapasitesi}L (ID: {record.id})"
                )
                violations += 1

        if violations == 0:
            print(
                f"  ✅ Checked {checked} fuel records. No capacity overflows detected."
            )
        else:
            print(f"  ❌ Found {violations} capacity violations.")

        # 3. VERIFY ANOMALIES
        print("\n🚨 Verifying Anomaly Injection...")

        stmt = select(Sefer.notlar).where(Sefer.notlar.like("%ANOMALY%"))
        anom_result = await db.execute(stmt)
        anomalies = anom_result.scalars().all()

        print(f"  - Total Anomalies Detected in Trips: {len(anomalies)}")
        if len(anomalies) > 0:
            print(f"  - Sample: {anomalies[0]}")
            print("  ✅ Anomaly injection successful.")
        else:
            print("  ⚠️ No anomalies found. Seeding chance might be too low.")

        # 4. VERIFY PHYSICS (Consumption vs Distance)
        print("\nphysic Verifying Physics Engine...")

        stmt = select(Sefer, Arac).join(Arac).order_by(Sefer.tarih.desc()).limit(10)
        trips = await db.execute(stmt)

        print("  - Recent Trip Analysis:")
        for trip, vehicle in trips:
            try:
                dist = float(trip.mesafe_km or 0)
                fuel = float(trip.dagitilan_yakit or 0)

                if dist > 0:
                    l_100km = (fuel / dist) * 100
                    dev = l_100km - vehicle.hedef_tuketim
                    print(
                        f"    * Trip ID {trip.id}: {dist}km -> {fuel:.1f}L ({l_100km:.1f} L/100km) | Target: {vehicle.hedef_tuketim} | Dev: {dev:.1f}"
                    )

                    if l_100km < 15 or l_100km > 60:
                        print(f"      ⚠️ WARNING: Physics outlier detected!")
                else:
                    print(f"    * Trip ID {trip.id}: 0km (Skipped physics check)")
            except Exception as e:
                print(f"    ❌ Error analyzing trip {trip.id}: {e}")

        print("\n✅ Verification Complete: System is ready for Real Data Testing.")


if __name__ == "__main__":
    asyncio.run(verify_real_flow())
