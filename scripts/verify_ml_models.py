import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from app.core.ml.model_manager import get_model_manager, ModelType
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


def verify_ml_models():
    print("Starting ML Model Verification (Ensemble)...")
    try:
        manager = get_model_manager()

        # Check Vehicle 1 (Demo Vehicle)
        # In a real scenario, we might iterate over all active vehicles.
        arac_id = 1

        version = manager.get_active_version(arac_id, ModelType.ENSEMBLE)

        if not version:
            print(f"WARN: No active ENSEMBLE model found for Vehicle {arac_id}.")
            print(
                "      This is expected if the system is fresh and no training has occurred."
            )
            print(
                "      To fix: Run 'await get_ensemble_service().train_for_vehicle(1)'"
            )
            # For verification purposes, we can't pass if there's no model,
            # BUT we don't want to block if it's just not trained yet.
            # Let's return False to prompt action, or True with warning?
            # User requirement: "verify_ml_models.py -> R² > 0.60"
            # If no model, R² is undefined.
            return False

        print(f"Model ID: {version.id}")
        print(f"Version: {version.version}")
        print(f"Type: {version.model_type}")
        print(f"Created At: {version.created_at}")
        print(f"Sample Count: {version.sample_count}")

        r2 = version.r2_score or 0.0
        print(f"R² Score: {r2:.4f}")

        if r2 >= 0.60:
            print("PASS: R² Score is above threshold (0.60).")
            return True
        else:
            print(f"FAIL: R² Score {r2:.4f} is below 0.60.")
            return False

    except Exception as e:
        print(f"FAIL: Exception during verification - {e}")
        # Print stack trace
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_ml_models()
    sys.exit(0 if success else 1)
