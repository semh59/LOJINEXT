import asyncio
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database.models import Sefer
from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
import pandas as pd
import sys

# Set standard output encoding to UTF-8 for Windows terminals
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Feature names from EnsembleFuelPredictor (16 features now)
FEATURE_NAMES = [
    "ton",
    "ascent_m",
    "descent_m",
    "net_elevation",
    "yuk_yogunlugu",
    "zorluk",
    "arac_yasi",
    "yas_faktoru",
    "mevsim_faktor",
    "sofor_katsayi",
    "motorway_ratio",
    "trunk_ratio",
    "primary_ratio",
    "residential_ratio",
    "unclassified_ratio",
    "flat_km",
]


async def analyze_impact():
    print("--- Feature Importance Impact Analysis (Residual Refactor) ---")

    # DB connection
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(Sefer).where(Sefer.tuketim != None))
        seferler_db = result.scalars().all()

    if not seferler_db:
        print("No trip data found with consumption. DB might be empty or not seeded.")
        return

    print(f"Total samples found: {len(seferler_db)}")

    # Prepare data
    seferler_data = []
    y_actual = []
    for s in seferler_db:
        seferler_data.append(
            {
                "mesafe_km": s.mesafe_km,
                "ton": s.ton,
                "ascent_m": s.ascent_m or 0,
                "descent_m": s.descent_m or 0,
                "flat_distance_km": s.flat_distance_km or 0,
                "zorluk": "Normal",
                "arac_yasi": 5,
                "rota_detay": s.rota_detay,
            }
        )
        y_actual.append(float(s.tuketim))

    # Initialize Predictor
    predictor = EnsembleFuelPredictor()

    # Train (Fit)
    predictor.fit(seferler_data, np.array(y_actual))

    if not predictor.is_trained:
        print("Training failed. Insufficient data or logic error.")
        return

    # Get Importances from RandomForest (Explainability baseline)
    importances = predictor.rf_model.feature_importances_

    df = pd.DataFrame(
        {"Feature": FEATURE_NAMES, "Importance": importances}
    ).sort_values(by="Importance", ascending=False)

    print("\n[SUCCESS] Feature Importance Rankings (distance excluded):")
    print(df.to_string(index=False))

    # Check if ton and elevation are now more important
    top_3 = df.head(3)["Feature"].tolist()
    print(f"\nTop 3 Impact Factors: {', '.join(top_3)}")

    # Verification against user concern:
    if "ton" in top_3 or "ascent_m" in top_3:
        print(
            "\n[DONE] SUCCESS: Ton or Elevation is now in Top 3. The model is no longer distance-blind."
        )
    else:
        print(
            "\n[WAIT] WARNING: Ton and Elevation are still low. Investigation needed."
        )


if __name__ == "__main__":
    asyncio.run(analyze_impact())
