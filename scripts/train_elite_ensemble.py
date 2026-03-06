import asyncio
import sys
import os

# Project Root
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.database.connection import AsyncSessionLocal
from app.database.models import Arac
from app.core.ml.ensemble_predictor import get_ensemble_service
from app.infrastructure.logging.logger import setup_logging
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = setup_logging("training")


def calculate_vif(df: pd.DataFrame):
    """
    Variance Inflation Factor (VIF) - Eş-doğrusallık tahlili.
    VIF > 10 ise yüksek multicollinearity vardır.
    """
    vif_data = pd.DataFrame()
    vif_data["feature"] = df.columns
    vif_values = []

    for feature in df.columns:
        X = df.drop(columns=[feature])
        y = df[feature]
        r2 = LinearRegression().fit(X, y).score(X, y)
        vif = 1 / (1 - r2) if r2 < 1 else float("inf")
        vif_values.append(vif)

    vif_data["VIF"] = vif_values
    return vif_data.sort_values("VIF", ascending=False)


async def train_elite_fleet():
    logger.info("Starting Elite Fleet Training (Refined)...")

    # Singleton service
    service = get_ensemble_service()

    async with AsyncSessionLocal() as session:
        # Get all vehicles
        vehicles_result = await session.execute(select(Arac).where(Arac.aktif))
        vehicles = vehicles_result.scalars().all()

        overall_stats = []

        for v in vehicles:
            logger.info(f"Training for Vehicle: {v.plaka} (ID: {v.id})")

            # Use the service's own training method to ensure consistency
            # train_for_vehicle handles: fetching, enrichment, fitting, saving
            result = await service.train_for_vehicle(v.id, include_synthetic=True)

            if result.get("success"):
                ensemble_r2 = result.get("ensemble_r2", 0)
                logger.info(f"  ✅ Training Success! Ensemble R2: {ensemble_r2:.4f}")

                # Check for other model scores
                models = ["gb_test_r2", "rf_test_r2", "xgb_r2", "lgb_r2"]
                scores = [
                    f"{m}: {result.get(m, 0):.3f}"
                    for m in models
                    if result.get(m) is not None
                ]
                logger.info(f"  📊 Detailed Scores: {', '.join(scores)}")

                overall_stats.append(ensemble_r2)

                # Phase 5A: VIF Analysis (Optional but recommended by expert)
                if result.get("feature_matrix") is not None:
                    try:
                        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

                        f_names = EnsembleFuelPredictor.FEATURE_NAMES
                        df_features = pd.DataFrame(
                            result["feature_matrix"], columns=f_names
                        )
                        vif_df = calculate_vif(df_features)

                        top_vif = vif_df.iloc[0]
                        if top_vif["VIF"] > 8:
                            logger.warning(
                                f"  ⚠️ High Multicollinearity: {top_vif['feature']} (VIF: {top_vif['VIF']:.2f})"
                            )
                        else:
                            logger.info(
                                f"  ✅ Feature Independence OK (Max VIF: {top_vif['VIF']:.2f})"
                            )
                    except Exception as e:
                        logger.error(f"  ❌ VIF Analysis Error: {e}")
            else:
                logger.error(f"  ❌ Training Failed: {result.get('error')}")

        # Train General Model (ID: 0)
        logger.info("Training General Fallback Model (ID: 0)...")
        # Note: train_general_model usually filters for 'is_real = TRUE',
        # but our synthesis uses 'is_real = FALSE'.
        # We might need to bypass this for the elite synthesis training.

        # Let's temporarily check train_general_model logic
        gen_result = await service.train_general_model(include_synthetic=True)
        logger.info(
            f"  General Model Training: {gen_result.get('success')} (Samples: {gen_result.get('sample_count')})"
        )

        if overall_stats:
            avg_r2 = sum(overall_stats) / len(overall_stats)
            logger.info("=" * 50)
            logger.info(f"FINAL AUDIT: Fleet Average R2 = {avg_r2:.4f}")
            if avg_r2 > 0.85:
                logger.info("💯 ELITE TARGET REACHED (>0.85)")
            else:
                logger.warning("⚠️ Elite target not fully reached, check data variance.")
            logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(train_elite_fleet())
