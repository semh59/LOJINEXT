import sys
import os
import json
import logging

# Add project root
sys.path.append(os.getcwd())

from app.core.ml.model_manager import get_model_manager, ModelType

# Configure logging
logging.basicConfig(level=logging.ERROR)


def show_scores():
    manager = get_model_manager()
    arac_id = 1
    model_type = ModelType.ENSEMBLE

    version = manager.get_active_version(arac_id, model_type)

    if not version:
        print("No active model found.")
        return

    print(f"Active Model ID: {version.id}")
    print(f"Version: {version.version}")

    try:
        params = json.loads(version.params_json)
        print("\n--- Model Component Scores ---")

        # XGBoost
        if "xgb_r2" in params:
            print(f"XGBoost R2 Score: {params['xgb_r2']}")

        # Gradient Boosting (sklearn)
        if "gb_cv_mean" in params:
            print(f"Gradient Boosting CV Score: {params['gb_cv_mean']}")

        # Random Forest
        if "rf_cv_mean" in params:
            print(f"Random Forest CV Score: {params['rf_cv_mean']}")

        # LightGBM
        if "lgb_r2" in params:
            print(f"LightGBM R2 Score: {params['lgb_r2']}")

        # Physics
        if "physics_mae" in params:
            print(f"Physics Model MAE: {params['physics_mae']}")

        print("\n--- All Utils ---")
        print(json.dumps(params, indent=2))

    except Exception as e:
        print(f"Error parsing params: {e}")


if __name__ == "__main__":
    show_scores()
