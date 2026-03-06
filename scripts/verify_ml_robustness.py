import asyncio
import sys
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
import xgboost as xgb
from typing import Dict, List

# Add project root
sys.path.append(os.getcwd())

from app.core.ml.ensemble_predictor import get_ensemble_service
from app.core.ml.physics_fuel_predictor import RouteConditions
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def verify_robustness():
    print("Starting ML Model Robustness Verification...")
    service = get_ensemble_service()
    arac_id = 1

    # 1. Fetch Data
    print(f"Fetching data for vehicle {arac_id}...")
    seferler = await service.sefer_repo.get_for_training(arac_id, limit=1000)

    if len(seferler) < 20:
        print(
            f"ERROR: Insufficient data. Found {len(seferler)} records. Need at least 20."
        )
        return

    print(f"Data count: {len(seferler)}")

    # 2. Prepare Feature Matrix (X) and Target (y)
    # We need to replicate the logic from EnsemblePredictor.fit roughly or use internal methods if possible.
    # Accessing internal logic via the service's predictor instance for consistency.
    predictor = service.get_predictor(arac_id)

    # Filter valid data
    valid_seferler = []
    y_actual = []

    for s in seferler:
        try:
            tuketim = float(s.get("tuketim") or 0)
            mesafe = float(s.get("mesafe_km") or 0)
            if tuketim > 0 and mesafe > 0:
                valid_seferler.append(s)
                y_actual.append(tuketim)
        except:
            continue

    if not valid_seferler:
        print("ERROR: No valid data after filtering.")
        return

    y_actual = np.array(y_actual)

    # Prepare X
    X = predictor.prepare_features(valid_seferler)

    # Physics Predictions (Calibrated)
    y_physics_total = []

    for s in valid_seferler:
        route = RouteConditions(
            distance_km=float(s.get("mesafe_km", 0) or 0),
            load_ton=float(s.get("ton", 0) or 0),
            is_empty_trip=False,
            ascent_m=float(s.get("ascent_m", 0) or 0),
            descent_m=float(s.get("descent_m", 0) or 0),
            flat_distance_km=float(s.get("flat_distance_km", 0) or 0),
        )
        pred = predictor.physics_model.predict(route)
        y_physics_total.append(pred.consumption_l_100km)

    y_physics_total = np.array(y_physics_total)
    y_l100km_actual = []
    for i, s in enumerate(valid_seferler):
        mesafe = float(s.get("mesafe_km"))
        tuketim = y_actual[i]
        y_l100km_actual.append((tuketim / mesafe) * 100)
    y_l100km_actual = np.array(y_l100km_actual)

    print(f"\n--- Unit Check ---")
    print(f"Sample Actual (L/100km): {y_l100km_actual[:5]}")
    print(f"Sample Physics (L/100km): {y_physics_total[:5]}")

    # Residuals (what models try to predict)
    residuals = y_l100km_actual - y_physics_total

    # 3. Train/Test Split
    (
        X_train,
        X_test,
        y_train_res,
        y_test_res,
        y_phys_train,
        y_phys_test,
        y_act_train,
        y_act_test,
    ) = train_test_split(
        X, residuals, y_physics_total, y_l100km_actual, test_size=0.2, random_state=42
    )

    # Scale features
    X_train_scaled = predictor.scaler.fit_transform(X_train)
    X_test_scaled = predictor.scaler.transform(X_test)

    print("\n--- Model Training & Evaluation (80% Train, 20% Test) ---")

    results = []

    # --- XGBoost ---
    xgb_model = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=2,
        learning_rate=0.05,
        min_child_weight=2,
        subsample=0.7,
        colsample_bytree=0.7,
        objective="reg:squarederror",
        random_state=42,
        verbosity=0,
    )
    xgb_model.fit(X_train_scaled, y_train_res)

    xgb_train_pred = xgb_model.predict(X_train_scaled)
    xgb_test_pred = xgb_model.predict(X_test_scaled)

    xgb_train_r2 = r2_score(y_train_res, xgb_train_pred)
    xgb_test_r2 = r2_score(y_test_res, xgb_test_pred)

    # Feature Importance (Explainability)
    # FEATURE_NAMES ile senkron (17 isim) — BUG-1 FIX
    importances = rf_model.feature_importances_
    # Note: ensemble_predictor has 16 features + 1 (flat_km) or similar.
    # Let's ensure length match.
    feature_names_to_use = predictor.FEATURE_NAMES

    results.append(
        {"Model": "XGBoost", "Train R2": xgb_train_r2, "Test R2": xgb_test_r2}
    )

    # --- Gradient Boosting ---
    gb_model = GradientBoostingRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.1, subsample=0.8, random_state=42
    )
    gb_model.fit(X_train_scaled, y_train_res)
    gb_train_r2 = r2_score(y_train_res, gb_model.predict(X_train_scaled))
    gb_test_r2 = r2_score(y_test_res, gb_model.predict(X_test_scaled))
    results.append(
        {"Model": "GradientBoosting", "Train R2": gb_train_r2, "Test R2": gb_test_r2}
    )

    # --- Random Forest ---
    rf_model = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
    rf_model.fit(X_train_scaled, y_train_res)
    rf_train_r2 = r2_score(y_train_res, rf_model.predict(X_train_scaled))
    rf_test_r2 = r2_score(y_test_res, rf_model.predict(X_test_scaled))
    results.append(
        {"Model": "RandomForest", "Train R2": rf_train_r2, "Test R2": rf_test_r2}
    )

    # --- Ensemble (Simulation) ---
    # Prediction = Physics + Model_Residual_Pred
    # Ensemble Residual Pred = 0.6*XGB + 0.1*GB + 0.1*RF + ...
    # We will verify if Ensemble is better on Test set

    ens_test_pred_res = (
        (
            0.60 * xgb_test_pred
            + 0.10 * gb_model.predict(X_test_scaled)
            + 0.10 * rf_model.predict(X_test_scaled)
        )
        / 0.80
    )  # Normalizing weights since we dropped lgb/physics weight from residual calc

    ens_test_r2 = r2_score(y_test_res, ens_test_pred_res)
    results.append(
        {"Model": "Ensemble (Simulated)", "Train R2": "-", "Test R2": ens_test_r2}
    )

    # --- Physics Report ---
    phys_mae = mean_absolute_error(y_act_test, y_phys_test)
    print(f"\n--- Physics Model verification (Test Set) ---")
    print(f"Physics MAE: {phys_mae:.2f} L/100km")

    # Display Results Table
    df = pd.DataFrame(results)
    print("\n--- Final Robustness Metrics ---")
    print(df.to_string(index=False))

    # Gap Analysis
    print("\n--- Overfitting Analysis ---")
    gap = xgb_train_r2 - xgb_test_r2
    if gap > 0.1:
        print(f"⚠️ XGBoost is Overfitting! Gap: {gap:.3f}")
    else:
        print(f"✅ XGBoost generalizes well. Gap: {gap:.3f}")


if __name__ == "__main__":
    asyncio.run(verify_robustness())
