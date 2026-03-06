import sys
import asyncio
import logging
from pathlib import Path
import numpy as np
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database.models import Sefer
from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    VehicleSpecs,
    RouteConditions,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_benchmark():
    """
    Gerçek sefer verileriyle Physics vs Ensemble modellerini karşılaştırır.
    """
    logger.info("Connecting to database (Async)...")
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        try:
            # 1. Gerçek tüketim verisi olan son 100 seferi çek
            logger.info("Fetching recent trips with fuel data...")
            stmt = (
                select(Sefer)
                .where(Sefer.tuketim > 0)
                .where(Sefer.mesafe_km > 0)
                .order_by(Sefer.tarih.desc())
                .limit(100)
            )
            result = await db.execute(stmt)
            seferler = result.scalars().all()

            if not seferler:
                logger.warning("No trips found with actual fuel data for benchmarking.")
                return

            logger.info(f"Found {len(seferler)} trips for benchmarking.")

            # 2. Modelleri hazırla
            physics_model = PhysicsBasedFuelPredictor(VehicleSpecs())
            results = []

            for sefer in seferler:
                arac_id = sefer.arac_id
                # DB'deki 'tuketim' alanı L/100km cinsindendir (Ground Truth)
                actual_l100km = float(sefer.tuketim)

                # Physics Prediction
                route = RouteConditions(
                    distance_km=float(sefer.mesafe_km),
                    load_ton=float(sefer.ton or 0),
                    is_empty_trip=False,
                    ascent_m=float(sefer.ascent_m or 0),
                    descent_m=float(sefer.descent_m or 0),
                )
                phys_pred = physics_model.predict(route)
                phys_l100km = phys_pred.consumption_l_100km

                # Ensemble Prediction
                ensemble_l100km = None
                ensemble_pred = EnsembleFuelPredictor()
                model_base = f"app/models/ensemble_v2_{arac_id}"

                # Check for meta file to confirm existence
                if Path(f"{model_base}_meta.json").exists():
                    try:
                        ensemble_pred.load_model(f"{model_base}.pkl")

                        # Prepare features (Must match prepare_features logic)
                        sefer_dict = {
                            "mesafe_km": float(sefer.mesafe_km),
                            "ton": float(sefer.ton or 0),
                            "ascent_m": float(sefer.ascent_m or 0),
                            "descent_m": float(sefer.descent_m or 0),
                            "flat_distance_km": float(sefer.flat_distance_km or 0),
                            "yas_faktoru": 1.0,
                            "mevsim_faktor": 1.0,
                            "rota_detay": sefer.rota_detay,  # Include route analysis
                        }
                        ens_result = ensemble_pred.predict(sefer_dict)
                        ensemble_l100km = ens_result.tahmin_l_100km
                    except Exception as e:
                        logger.warning(f"Failed to predict for vehicle {arac_id}: {e}")

                results.append(
                    {
                        "id": sefer.id,
                        "actual": actual_l100km,
                        "physics": phys_l100km,
                        "ensemble": ensemble_l100km,
                    }
                )

            # 3. Metrikleri Hesapla
            phys_errors = [r["physics"] - r["actual"] for r in results]
            phys_mae = np.mean(np.abs(phys_errors))
            phys_rmse = np.sqrt(np.mean(np.array(phys_errors) ** 2))

            ens_results = [r for r in results if r["ensemble"] is not None]
            ens_mae = None
            if ens_results:
                ens_errors = [r["ensemble"] - r["actual"] for r in ens_results]
                ens_mae = np.mean(np.abs(ens_errors))
                ens_rmse = np.sqrt(np.mean(np.array(ens_errors) ** 2))

            # 4. Raporla
            print("\n" + "=" * 50)
            print("LOJINEXT FUEL PREDICTION BENCHMARK")
            print("=" * 50)
            print(f"Total Trips Evaluated: {len(results)}")
            print("-" * 30)
            print("PHYSICS MODEL (Baseline):")
            print(f"  MAE:  {phys_mae:.2f} L/100km")
            print(f"  RMSE: {phys_rmse:.2f} L/100km")
            print("-" * 30)
            if ens_mae is not None:
                print("ENSEMBLE MODEL (Active):")
                print(f"  Count: {len(ens_results)}")
                print(f"  MAE:  {ens_mae:.2f} L/100km")
                print(f"  RMSE: {ens_rmse:.2f} L/100km")
                improvement = (
                    ((phys_mae - ens_mae) / phys_mae) * 100 if phys_mae > 0 else 0
                )
                print(f"  Improvement (MAE): {improvement:.1f}%")
            else:
                print("ENSEMBLE MODEL: No trained models found for these trips.")
            print("=" * 50 + "\n")

        except Exception as e:
            logger.error(f"Benchmark failed: {e}", exc_info=True)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_benchmark())
