import sys
import os
import json
import logging

# Add project root
sys.path.append(os.getcwd())

from app.core.ml.model_manager import get_model_manager, ModelType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_save():
    print("Testing ModelManager.save_version...")
    manager = get_model_manager()

    arac_id = 1
    model_type = ModelType.ENSEMBLE
    params = {"test": "data", "success": True}
    metrics = {"r2_score": 0.99, "mae": 1.5, "sample_count": 100}

    try:
        version_id = manager.save_version(
            arac_id=arac_id,
            model_type=model_type,
            params=params,
            metrics=metrics,
            notes="Manual Verification",
        )
        print(f"SUCCESS: Saved version {version_id}")
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_save()
