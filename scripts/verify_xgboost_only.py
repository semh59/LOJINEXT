import asyncio
import sys
import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_absolute_error

# Add project root
sys.path.append(os.getcwd())

from app.core.ml.ensemble_predictor import get_ensemble_service
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


async def verify_xgboost_only():
    print("Starting Phase 2D: XGBoost-Only Reality Check...")
    service = get_ensemble_service()
    arac_id = 1

    # 1. Fetch Data
    print(f"Fetching data for vehicle {arac_id}...")
    seferler = await service.sefer_repo.get_for_training(arac_id, limit=1000)

    if len(seferler) < 5:
        print(
            f"ERROR: Insufficient data. Found {len(seferler)} records. Need at least 5 for CV."
        )
        return

    print(f"Data count: {len(seferler)}")

    # 2. Prepare Data
    predictor = service.get_predictor(arac_id)
    valid_seferler = []
    y_actual = []

    for s in seferler:
        try:
            tuketim = float(s.get("tuketim") or 0)
            mesafe = float(s.get("mesafe_km") or 0)
            if tuketim > 0 and mesafe > 0:
                valid_seferler.append(s)
                # Target: L/100km
                y_actual.append((tuketim / mesafe) * 100)
        except:
            continue

    if not valid_seferler:
        print("ERROR: No valid data after filtering.")
        return

    y = np.array(y_actual)
    X = predictor.prepare_features(valid_seferler)
    X_scaled = predictor.scaler.fit_transform(X)

    print(f"Target Mean (L/100km): {np.mean(y):.2f}")
    print(f"Target Std  (L/100km): {np.std(y):.2f}")

    # 3. Initialize XGBoost (Simple Regressor)
    # Using 'reg:squarederror' as objective
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

    # 4. 5-Fold Cross Validation
    print("\n--- 5-Fold Cross Validation ---")
    kf = KFold(n_splits=min(5, len(y)), shuffle=True, random_state=42)

    cv_scores = cross_val_score(xgb_model, X_scaled, y, cv=kf, scoring="r2")
    cv_mae = -cross_val_score(
        xgb_model, X_scaled, y, cv=kf, scoring="neg_mean_absolute_error"
    )

    print(f"CV R² Scores: {cv_scores}")
    print(f"Mean CV R²:   {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    print(f"Mean CV MAE:  {cv_mae.mean():.2f} L/100km")

    # 5. Feature Importance
    print("\n--- Feature Importance ---")
    xgb_model.fit(X_scaled, y)

    feature_names = predictor.FEATURE_NAMES
    importances = xgb_model.feature_importances_
    indices = np.argsort(importances)[::-1]

    for f in range(X.shape[1]):
        print(f"{f + 1}. {feature_names[indices[f]]}: {importances[indices[f]]:.4f}")

    # 6. Conclusion
    print("\n--- Conclusion ---")
    if cv_scores.mean() < 0.5:
        print("🔴 Weak correlation. More data needed.")
    elif cv_scores.mean() < 0.7:
        print("🟡 Moderate correlation. Acceptable for baseline.")
    else:
        print("🟢 Strong correlation (Suspiciously high if N < 100).")


if __name__ == "__main__":
    asyncio.run(verify_xgboost_only())
