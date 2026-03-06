from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
import tempfile
import shutil
from pathlib import Path
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)


def run():
    p = EnsembleFuelPredictor()
    seferler = [{"mesafe_km": 100, "ton": 10}] * 15
    y_actual = np.array([30.0] * 15)
    p.fit(seferler, y_actual)

    tmp_dir = tempfile.mkdtemp()
    try:
        path = Path(tmp_dir) / "test_model"
        print(f"Saving to {path}")
        res = p.save_model(str(path))
        print(f"Save result: {res}")

        load_res = p.load_model(str(path))
        print(f"Load result: {load_res}")
        print(f"Load result type: {type(load_res)}")
    finally:
        shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    run()
