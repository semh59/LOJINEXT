import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.core.ml.ensemble_predictor import get_ensemble_service
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def train_demo_model():
    print("Starting Demo Model Training (Vehicle 1)...")
    try:
        service = get_ensemble_service()

        # Trigger training for Vehicle 1
        # This will fetch data from DB (if any) or fail if no trips.
        # But we need data to train!
        # If no data, we can't train.
        # We should check if we have trips.
        # Data integrity check said we have duplicate trips (which means we have data).

        arac_id = 1
        result = await service.train_for_vehicle(arac_id)

        print(f"Training Result: {result}")

        if result.get("success"):
            print("PASS: Model trained successfully.")
            return True
        else:
            print(f"FAIL: Training failed - {result.get('error')}")
            # If failed due to no data, we might need to seed data?
            # Creating dummy trips?
            return False

    except Exception as e:
        print(f"FAIL: Exception during training - {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(train_demo_model())
    sys.exit(0 if success else 1)
