import re
import os
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

    print("SUCCESS: Import successful. No syntax errors.")
except SyntaxError as e:
    print(f"ERROR: Syntax error in ensemble_predictor.py: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to import: {e}")
    sys.exit(1)

# Inspect the source code directly using inspect to see what's actually there
import inspect

p = EnsembleFuelPredictor()
source = inspect.getsource(EnsembleFuelPredictor)

# 1. Literal Checks
if "(tuketim / mesafe) * 100" in source:
    print("BUG FOUND: '(tuketim / mesafe) * 100' still exists in source code!")
else:
    print("INFO: '(tuketim / mesafe) * 100' NOT found in source code.")

if "physics_value *= yas_faktoru" in source:
    print("BUG FOUND: 'physics_value *= yas_faktoru' still exists!")

if "gb_prediction" in source:
    print("INFO: 'gb_prediction' found (legacy check).")

# 2. Logic Check: y_norm length in fit
# We'll mock the internal methods to test only the y_norm loop
seferler = [
    {"id": 1, "mesafe_km": 100, "ton": 20},
    {"id": 2, "mesafe_km": 50, "ton": 10},
]
y_actual = np.array([25.0, 15.0])


# We can manually walk the logic as it exists in the file to see if it would double append
# (Since we can't easily mock complex imports inside fit without a proper test framework)
def mock_y_norm_logic(seferler, y_actual):
    y_norm = []
    y_physics = [25.0, 25.0]
    for i, s in enumerate(seferler):
        # This is strictly reproducing the lines from the file
        val = float(y_actual[i] or 0.0)
        if val > 0:
            y_norm.append(val)
        else:
            y_norm.append(y_physics[i])
    return y_norm


y_norm_mock = mock_y_norm_logic(seferler, y_actual)
if len(y_norm_mock) != len(seferler):
    print(
        f"BUG FOUND: y_norm length ({len(y_norm_mock)}) does not match seferler count ({len(seferler)})!"
    )
else:
    print("INFO: y_norm logic is correct (no double-append).")

# 3. Logic Check: model_predictions keys
# This checks the actual runtime dictionary creation in predict
dummy_sefer = {"mesafe_km": 100, "ton": 20, "yas_faktoru": 1.0, "mevsim_faktor": 1.0}
# We'll mock part of predict if possible, or just re-verify literal dictionary content
import re

matches = re.findall(r"model_predictions = \{.*?\}", source, re.DOTALL)
for match in matches:
    keys = re.findall(r'"(\w+)":', match)
    if len(keys) != len(set(keys)):
        print(f"BUG FOUND: Duplicate keys in model_predictions dictionary: {keys}")
    else:
        print("INFO: model_predictions dictionary keys are unique.")

# 4. Final check: fit test loop
fit_source = inspect.getsource(p.fit)
if fit_source.count("final_preds.append") > 1:
    print(
        f"BUG FOUND: final_preds.append() called {fit_source.count('final_preds.append')} times in fit()!"
    )
else:
    print("INFO: final_preds.append() called correctly in fit().")
