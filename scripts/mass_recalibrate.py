import asyncio
import os
import sys

from dotenv import load_dotenv

from app.core.ml.ensemble_predictor import EnsemblePredictorService
from app.infrastructure.logging.logger import get_logger

# Add project root to path (if not using PYTHONPATH)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment
load_dotenv(os.path.join(project_root, ".env"))

logger = get_logger(__name__)


async def mass_recalibrate():
    """Retrain all vehicles and General model using Split-Validation."""
    predictor_service = EnsemblePredictorService()

    # 1. Train General Model (fallback)
    print("--- Training General Model ---")
    gen_res = await predictor_service.train_general_model()
    if gen_res.get("success"):
        print(f"General Model R2: {gen_res.get('gb_test_r2', 'N/A')}")

    # 2. Train All Vehicles (Mass Retrain script logic)
    # This will now use the new honest R2 logic automatically
    from scripts.train_model_with_route_features import train_all_vehicles

    await train_all_vehicles()


if __name__ == "__main__":
    asyncio.run(mass_recalibrate())
