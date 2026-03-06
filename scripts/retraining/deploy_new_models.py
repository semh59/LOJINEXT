import shutil
import os
import glob
from datetime import datetime


def deploy_models():
    """
    Yeni modelleri production klasörüne deploy et
    """
    print("\n🚀 DEPLOYING NEW MODELS (v3)...")

    model_dir = "app/core/ml/models"
    backup_dir = f"app/core/ml/models/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 1. Backup
    if os.path.exists(model_dir):
        os.makedirs(backup_dir, exist_ok=True)
        for f in glob.glob(f"{model_dir}/vehicle_*.pkl"):
            if "_v3" not in f:  # Backup non-v3 models
                shutil.copy(f, backup_dir)
        print(f"✅ Backed up existing models to {backup_dir}")

    # 2. Activate v3 (Rename or just keep as is if EnsemblePredictor looks for them)
    # The current code in EnsembleFuelPredictor looks for models.
    # We should ensure the filenames match what the app expects.
    # If app expects 'vehicle_1.pkl' but we have 'vehicle_1_v3.pkl', we should rename.

    # Let's check EnsembleFuelPredictor.get_model_path logic.
    # Assuming it looks for vehicle_{id}.pkl

    v3_models = glob.glob(f"{model_dir}/vehicle_*_v3.pkl")
    for v3_file in v3_models:
        base_name = os.path.basename(v3_file).replace("_v3", "")
        dest = os.path.join(model_dir, base_name)
        shutil.copy(v3_file, dest)
        print(f"  🚀 Activated: {v3_file} -> {dest}")

    print("\n✅ DEPLOYMENT COMPLETE!")


if __name__ == "__main__":
    deploy_models()
