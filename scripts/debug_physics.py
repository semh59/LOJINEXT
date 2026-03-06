import sys
import os
import asyncio

sys.path.append(os.getcwd())

from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    VehicleSpecs,
    RouteConditions,
)
from app.database.connection import AsyncSessionLocal
from app.database.repositories.sefer_repo import get_sefer_repo


async def debug_physics():
    print("🔬 Debugging Physics Model SINGLE TRIP Trace...")

    # 1. Get a real trip with enriched data
    async with AsyncSessionLocal() as session:
        repo = get_sefer_repo(session)
        # Get Istanbul-Ankara trip (ID 1 from Step 426 was 480km, 37.08L)
        # We need check if it has ascent populated in Sefer or Lokasyon match
        trips = await repo.get_for_training(arac_id=21, limit=1)
        if not trips:
            print("❌ No data found.")
            return

        t = trips[0]
        print(f"📄 Trip Data: {t}")

    # 2. Setup Physics Model
    # Vehicle 21: Mercedes-Benz Actros 1845
    specs = VehicleSpecs(
        empty_weight_kg=8000,
        drag_coefficient=0.6,  # Modern truck
        frontal_area_m2=9.0,
        rolling_resistance=0.006,
        engine_efficiency=0.40,
    )
    predictor = PhysicsBasedFuelPredictor(vehicle=specs)

    # 3. Create Route Conditions
    # CAUTION: 'ascent_m' might be huge (7200)
    route = RouteConditions(
        distance_km=float(t["mesafe_km"]),
        load_ton=float(t["ton"]),
        ascent_m=float(t["ascent_m"]),
        descent_m=float(t["descent_m"]),
        avg_speed_kmh=75.0,  # Typical highway speed
        road_quality=1.0,
    )

    print(f"\n🛣️ Route Conditions: {route}")

    # 4. Predict and Trace
    pred = predictor.predict(route)

    print(f"\n🔮 Prediction Result:")
    print(f"   Consumed: {pred.total_liters} L")
    print(f"   Rate: {pred.consumption_l_100km} L/100km")
    print(f"   Breakdown: {pred.energy_breakdown}")

    actual = t["tuketim"]
    print(f"\n📏 Actual: {actual} L/100km")
    print(f"❌ Error: {pred.consumption_l_100km - actual:.2f} L/100km")

    # Analysis
    if pred.consumption_l_100km > actual + 10:
        print("⚠️ OVER-PREDICTION DETECTED. Check Gravity/Ascent.")
    elif pred.consumption_l_100km < actual - 10:
        print("⚠️ UNDER-PREDICTION DETECTED. Check Rolling/Air.")


if __name__ == "__main__":
    asyncio.run(debug_physics())
