import asyncio
import sys
import os
from datetime import date

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.prediction_service import get_prediction_service
from app.database.repositories.arac_repo import get_arac_repo


async def perform_ai_robustness_audit():
    print("🧠 Starting ELITE AI Model Robustness & Edge-Case Audit...")

    pred_service = get_prediction_service()

    # Get a valid vehicle
    vehicles = await get_arac_repo().get_all(limit=1)
    if not vehicles:
        print("❌ Error: No vehicles found.")
        return
    arac_id = vehicles[0]["id"]

    edge_cases = [
        ("Zero Distance", {"mesafe_km": 0.0, "ton": 10.0}),
        ("Extreme Load (100 Tons)", {"mesafe_km": 100.0, "ton": 100.0}),
        (
            "Negative Altitude (Deep Sea Drive?)",
            {"mesafe_km": 100.0, "ton": 20.0, "ascent_m": -1000},
        ),
        (
            "Empty Trip Flag with Load",
            {"mesafe_km": 100.0, "ton": 20.0, "bos_sefer": True},
        ),
        (
            "Far Future Date",
            {"mesafe_km": 100.0, "ton": 10.0, "target_date": date(2030, 1, 1)},
        ),
    ]

    for name, params in edge_cases:
        print(f"\n🧪 Testing Edge Case: {name}")
        try:
            prediction = await pred_service.predict_consumption(
                arac_id=arac_id, **params
            )
            print(
                f"   ✅ Result: {prediction.get('prediction_liters')} Liters ({prediction.get('method')})"
            )

            # Sanity check
            liters = prediction.get("prediction_liters", 0)
            if liters < 0:
                print(f"   ❌ FAILED: Negative fuel prediction returned!")
            elif liters == 0 and params.get("mesafe_km", 0) > 0:
                print(f"   ⚠️ WARNING: Zero fuel predicted for positive distance.")
            else:
                print(f"   🌟 SUCCESS: Model handled edge case gracefully.")

        except Exception as e:
            print(f"   ❌ CRITICAL FAILURE: Model crashed on edge case: {e}")


if __name__ == "__main__":
    asyncio.run(perform_ai_robustness_audit())
