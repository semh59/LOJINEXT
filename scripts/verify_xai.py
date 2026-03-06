import os
import sys
import asyncio

# Mock environment
os.environ["ENVIRONMENT"] = "dev"
os.environ["SECRET_KEY"] = "dev_secret_key_change_me_in_prod"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:!23efe25ali!@localhost:5432/tir_yakit"
)
os.environ["OPENROUTESERVICE_API_KEY"] = "test_key"

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


async def test_xai_logic():
    try:
        from app.services.prediction_service import PredictionService

        service = PredictionService()

        # Sample request
        test_req = {
            "arac_id": 1,
            "mesafe_km": 450,
            "ton": 15.5,
            "ascent_m": 850,
            "descent_m": 400,
            "zorluk": "Zor",
            "sofor_score": 0.85,
        }

        print("Requesting explanation...")
        explanation = await service.explain_consumption(**test_req)

        if "prediction" in explanation and "contributions" in explanation:
            print("[SUCCESS] XAI Logic Test: PASSED")
            print(f"Prediction: {explanation['prediction']} {explanation['unit']}")
            print("Contributions:")
            for feature, impact in explanation["contributions"].items():
                print(f"  - {feature}: {impact} L/100km")
        else:
            print(
                f"[FAILURE] XAI Logic Test: FAILED. Unexpected response: {explanation}"
            )

    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_xai_logic())
