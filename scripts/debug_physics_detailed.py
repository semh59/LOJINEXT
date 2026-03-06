import asyncio
import sys
import os
import pandas as pd
import numpy as np

# Add project root
sys.path.append(os.getcwd())

from app.core.ml.ensemble_predictor import get_ensemble_service
from app.core.ml.physics_fuel_predictor import RouteConditions
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def debug_physics_inputs():
    print("Starting Physics Model Detailed Debugging...")
    service = get_ensemble_service()
    arac_id = 1

    # 1. Fetch Data
    print(f"Fetching data for vehicle {arac_id}...")
    seferler = await service.sefer_repo.get_for_training(
        arac_id, limit=20
    )  # Check first 20

    if not seferler:
        print("No data found.")
        return

    print(f"Found {len(seferler)} records. Analyzing inputs for first 5...")

    predictor = service.get_predictor(arac_id)

    for i, s in enumerate(seferler[:5]):
        print(f"\n--- Record {i + 1} ---")

        # Raw Inputs
        tuketim = float(s.get("tuketim") or 0)
        mesafe = float(s.get("mesafe_km") or 0)
        ton = float(s.get("ton") or 0)
        ascent = float(s.get("ascent_m") or 0)
        descent = float(s.get("descent_m") or 0)

        print(f"INPUTS: Distance={mesafe} km, Load={ton} ton")
        print(f"        Ascent={ascent} m, Descent={descent} m")
        print(f"        Actual Consumption: {tuketim} L")

        if mesafe > 0:
            actual_l100 = (tuketim / mesafe) * 100
            print(f"        Actual L/100km: {actual_l100:.2f}")
        else:
            print("        Actual L/100km: N/A (Dist=0)")
            continue

        # Prepare Route
        route = RouteConditions(
            distance_km=mesafe,
            load_ton=ton,
            is_empty_trip=False,  # Assuming false for now based on current logic
            ascent_m=ascent,
            descent_m=descent,
            flat_distance_km=float(s.get("flat_distance_km") or 0),
        )

        # Physics Prediction
        pred = predictor.physics_model.predict(route)

        print(f"OUTPUT: Physics Total Liters: {pred.total_liters}")
        print(f"        Physics L/100km: {pred.consumption_l_100km}")
        print(f"        Energy Breakdown: {pred.energy_breakdown}")

        # Anomaly Check
        if pred.consumption_l_100km > 40:
            print("⚠️  HIGH PREDICTION! Checking contributors...")
            if pred.energy_breakdown["tirmanis"] > 40:
                print("    -> Climbing cost is unusually high. Check 'ascent_m'.")
            if pred.energy_breakdown["yuvarlanma"] > 40:
                print("    -> Rolling resistance is high. Check 'ton' or coefficients.")


if __name__ == "__main__":
    asyncio.run(debug_physics_inputs())
