import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.core.ml.ensemble_predictor import EnsembleFuelPredictor


def debug_load():
    p = EnsembleFuelPredictor()
    path = "tests/dummy_model.json"
    print(f"Testing load_model with {path}")
    try:
        res = p.load_model(path)
        print(f"Return type: {type(res)}")
        print(f"Return value: {res}")
    except Exception as e:
        print(f"Exception caught: {e}")


if __name__ == "__main__":
    debug_load()
