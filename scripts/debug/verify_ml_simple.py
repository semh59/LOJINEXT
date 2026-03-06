import asyncio
import sys
import os
import numpy as np
import warnings
from sqlalchemy import select
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

# Suppress warnings
warnings.filterwarnings("ignore")

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.database.models import Sefer, Arac
from app.core.ml.ensemble_predictor import VehicleSpecs


async def verify_simple_models():
    print("🧪 Benchmarking Simpler Models...")
    print("=================================")

    async with AsyncSessionLocal() as db:
        # 1. Fetch Data
        stmt = select(Sefer, Arac).join(Arac).where(Sefer.mesafe_km > 0).limit(1000)
        result = await db.execute(stmt)
        rows = result.all()

        # Group by Vehicle
        vehicle_data = {}
        for trip, vehicle in rows:
            if vehicle.id not in vehicle_data:
                vehicle_data[vehicle.id] = {"X": [], "y": [], "raw": []}

            # Simple Features
            # Physics-informed features: Load * Distance, Grade, etc.
            # But here we just use what we have:
            # [mesafe, ton] -> tuketim

            features = [
                float(trip.mesafe_km),
                float(trip.ton),
            ]
            vehicle_data[vehicle.id]["X"].append(features)
            vehicle_data[vehicle.id]["y"].append(float(trip.tuketim))

        print(f"📊 Analyzing {len(vehicle_data)} vehicles...")

        results = []

        for vid, data in vehicle_data.items():
            X = np.array(data["X"])
            y = np.array(data["y"])

            n_samples = len(y)
            if n_samples < 10:
                continue

            # Split 80/20
            split = int(n_samples * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]

            if len(y_test) < 2:
                continue

            # 1. Linear Regression
            lin_model = LinearRegression()
            lin_model.fit(X_train, y_train)
            lin_pred = lin_model.predict(X_test)
            lin_r2 = r2_score(y_test, lin_pred)
            lin_mae = mean_absolute_error(y_test, lin_pred)

            # 2. Simple XGBoost
            xgb_simple = XGBRegressor(
                n_estimators=50,
                max_depth=2,
                learning_rate=0.05,
                min_child_weight=2,
                subsample=0.7,
                colsample_bytree=0.7,
                verbosity=0,
            )
            xgb_simple.fit(X_train, y_train)
            xgb_pred = xgb_simple.predict(X_test)
            xgb_r2 = r2_score(y_test, xgb_pred)
            xgb_mae = mean_absolute_error(y_test, xgb_pred)

            # 3. Overfitted XGBoost
            xgb_overfit = XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1, verbosity=0
            )
            xgb_overfit.fit(X_train, y_train)
            xgb_overfit_test_pred = xgb_overfit.predict(X_test)
            xgb_overfit_train_pred = xgb_overfit.predict(X_train)

            xgb_of_train_r2 = r2_score(y_train, xgb_overfit_train_pred)
            xgb_of_test_r2 = r2_score(y_test, xgb_overfit_test_pred)
            xgb_of_test_mae = mean_absolute_error(y_test, xgb_overfit_test_pred)

            results.append(
                {
                    "vid": vid,
                    "n": n_samples,
                    "linear_r2": lin_r2,
                    "linear_mae": lin_mae,
                    "simple_xgb_r2": xgb_r2,
                    "simple_xgb_mae": xgb_mae,
                    "overfit_train_r2": xgb_of_train_r2,
                    "overfit_test_r2": xgb_of_test_r2,
                    "overfit_test_mae": xgb_of_test_mae,
                }
            )

        # Report
        avg_lin_r2 = np.mean([r["linear_r2"] for r in results])
        avg_lin_mae = np.mean([r["linear_mae"] for r in results])

        avg_simple_xgb_r2 = np.mean([r["simple_xgb_r2"] for r in results])
        avg_simple_xgb_mae = np.mean([r["simple_xgb_mae"] for r in results])

        avg_of_train_r2 = np.mean([r["overfit_train_r2"] for r in results])
        avg_of_test_r2 = np.mean([r["overfit_test_r2"] for r in results])
        avg_of_test_mae = np.mean([r["overfit_test_mae"] for r in results])

        print("\n📈 Detailed Benchmark Results (Avg across vehicles):")
        print(f"  - Samples per Vehicle: ~{int(np.mean([r['n'] for r in results]))}")
        print("--------------------------------------------------")
        print(f"  ❌ Complex XGBoost (Overfit):")
        print(f"     Train R2 : {avg_of_train_r2:.3f}")
        print(f"     Test R2  : {avg_of_test_r2:.3f}")
        print(f"     Test MAE : {avg_of_test_mae:.2f} L/100km")
        print("--------------------------------------------------")
        print(f"  ✅ Linear Regression:")
        print(f"     Test R2  : {avg_lin_r2:.3f}")
        print(f"     Test MAE : {avg_lin_mae:.2f} L/100km")
        print("--------------------------------------------------")
        print(f"  ✅ Simple XGBoost (Optimized):")
        print(f"     Test R2  : {avg_simple_xgb_r2:.3f}")
        print(f"     Test MAE : {avg_simple_xgb_mae:.2f} L/100km")

        if avg_simple_xgb_mae < avg_lin_mae:
            print("\n💡 Winner: Simple XGBoost (Lower Error)")
            print("   Action: Swapping complex ensemble for Linear/Simple XGB.")
        else:
            print("\n💡 Winner: Linear Regression (Lower Error)")
            print("   Action: Swapping complex ensemble for Linear/Simple XGB.")


if __name__ == "__main__":
    asyncio.run(verify_simple_models())
