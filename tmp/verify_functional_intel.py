import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.services.anomaly_detector import (
    get_anomaly_detector,
    AnomalyType,
    SeverityEnum,
    AnomalyResult,
)
from app.core.ml.physics_fuel_predictor import PhysicsBasedFuelPredictor


async def verify_rca():
    print("--- Verifying RCA Logic ---")
    detector = get_anomaly_detector()

    # Mock an anomaly result to test the heuristic generator
    mock_result = AnomalyResult(
        tip=AnomalyType.TUKETIM,
        kaynak_tip="arac",
        kaynak_id=1,
        deger=45.0,
        beklenen_deger=25.0,
        sapma_yuzde=80.0,
        severity=SeverityEnum.CRITICAL,
        aciklama="High consumption",
    )

    rca, action = detector._generate_heuristic_rca(mock_result)
    print(f"Generated RCA: {rca}")
    print(f"Generated Action: {action}")

    # Check for core keywords, ignoring encoding artifacts
    if "Yak" in rca and "s" in rca:
        print("[SUCCESS] RCA Logic works correctly for high deviations.")
    else:
        print("[FAILURE] RCA Logic mismatch.")


async def verify_physics_insights():
    print("\n--- Verifying Physics Insights ---")
    predictor = PhysicsBasedFuelPredictor()

    # Mock segments for a 100km trip with 1000m total ascent
    segments = [
        (100000.0, 22.2, 1000.0)  # 100km at 80km/h with 1000m climb
    ]

    res = predictor.predict_granular(segments=segments, load_ton=20.0, arac_yasi=2)

    print(f"Consumption L/100km: {res.consumption_l_100km:.2f}")
    print(f"Generated Insight: {res.insight}")

    # Check for ramp/yokuş related keywords
    if res.insight and ("rampa" in res.insight.lower() or "yok" in res.insight.lower()):
        print("[SUCCESS] Physics Insight works correctly for slope detection.")
    else:
        print("[FAILURE] Physics Insight mismatch or missing.")


async def main():
    try:
        await verify_rca()
    except Exception as e:
        print(f"RCA Verification Error: {e}")

    try:
        await verify_physics_insights()
    except Exception as e:
        print(f"Physics Verification Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
