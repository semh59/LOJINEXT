import os
import sys
import asyncio
import json

# Mock environment
os.environ["ENVIRONMENT"] = "dev"
os.environ["SECRET_KEY"] = "dev_secret_key_change_me_in_prod"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:!23efe25ali!@localhost:5432/tir_yakit"
)

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


async def run_scenario(name, req_data):
    from app.services.prediction_service import PredictionService

    service = PredictionService()

    print(f"\n>>> Running Scenario: {name}")
    print(f"Params: {req_data}")

    try:
        # Prediction (Filter out 'zorluk' as predict_consumption doesn't take it directly)
        predict_params = req_data.copy()
        zorluk_val = predict_params.pop("zorluk", "Normal")

        pred = await service.predict_consumption(**predict_params)
        print(
            f"Prediction result: {pred['tahmini_tuketim']} L/100km (Model: {pred['model_used']})"
        )

        # Explanation
        expl = await service.explain_consumption(**req_data)

        print("XAI Contributions:")
        for feat, impact in expl["contributions"].items():
            dir_str = "INCREASE" if impact > 0 else "DECREASE"
            print(f"  - {feat:20}: {impact:+.2f} L/100km ({dir_str})")

        return expl
    except Exception as e:
        print(f"Error in scenario {name}: {e}")
        return None


async def main():
    print("=" * 60)
    print("LOJINEXT EXTENDED XAI DEEP VERIFICATION")
    print("=" * 60)

    # Scenario 1: Reference (Empty Trip)
    base_req = {
        "arac_id": 1,
        "mesafe_km": 500,
        "ton": 0,
        "ascent_m": 0,
        "descent_m": 0,
        "zorluk": "Normal",
        "sofor_score": 1.0,
    }
    res_empty = await run_scenario("Reference (Empty Trip)", base_req)

    # Scenario 2: Heavy Load
    heavy_req = base_req.copy()
    heavy_req["ton"] = 25.0
    res_heavy = await run_scenario("Heavy Load (25 Ton)", heavy_req)

    # Scenario 3: Steep Ascent
    climb_req = heavy_req.copy()
    climb_req["ascent_m"] = 1200
    res_climb = await run_scenario("Steep Ascent (1200m)", climb_req)

    # Scenario 4: Poor Driver Performance
    bad_driver_req = climb_req.copy()
    bad_driver_req["sofor_score"] = 0.5
    res_bad_driver = await run_scenario(
        "Poor Driver Performance (Score 0.5)", bad_driver_req
    )

    print("\n" + "=" * 60)
    print("CONSISTENCY CHECKS")
    print("=" * 60)

    if res_heavy and res_empty:
        # Load contribution should be visible in heavy trip
        load_impact = res_heavy["contributions"].get("Yük", 0)
        if load_impact > 0:
            print("[PASS] Load contribution logic is consistent.")
        else:
            print("[FAIL] Load impact not detected or negative in heavy scenario.")

    if res_climb and res_heavy:
        climb_impact = res_climb["contributions"].get("Yol Eğimi (Çıkış)", 0)
        if climb_impact > 0:
            print("[PASS] Ascent contribution logic is consistent.")
        else:
            print("[FAIL] Ascent impact not detected or negative in climb scenario.")

    print("\nDeep verification complete.")


if __name__ == "__main__":
    asyncio.run(main())
