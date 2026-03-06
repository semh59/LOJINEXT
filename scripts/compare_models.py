import asyncio
import os
import sys

from sklearn.metrics import mean_absolute_error, r2_score
from sqlalchemy import select

from app.core.ml.ensemble_predictor import get_ensemble_service
from app.database.connection import AsyncSessionLocal
from app.database.models import Sefer

# Add project root to path (if not using PYTHONPATH)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


async def compare_models_optimized():
    """
    Optimized comparison script using a shared session.
    """
    print("\n" + "=" * 50)
    print("📈 LOJINEXT ML PERFORMANCE AUDIT (Optimized)")
    print("=" * 50)

    ensemble_service = get_ensemble_service()

    async with AsyncSessionLocal() as session:
        # 1. Test verisi çek (Araç ID=4)
        target_arac_id = 4
        stmt = select(Sefer).where(
            Sefer.arac_id == target_arac_id, Sefer.durum == "Tamam"
        )
        result = await session.execute(stmt)
        sefer_list = result.scalars().all()

        if len(sefer_list) < 10:
            print(f"❌ Araç {target_arac_id} için yeterli veri yok.")
            return

        print(f"Analyzing {len(sefer_list)} trips for Vehicle {target_arac_id}...")

        # 2. Gerçek değerler
        y_true = [float(s.tuketim) for s in sefer_list]

        # 3. Yeni Model Tahminleri
        # Predictor'ı bir kez alalım
        predictor = ensemble_service.get_predictor(target_arac_id)

        # Eğer model eğitilmemişse eğit (Fallback)
        if not predictor.is_trained:
            print("Model not trained, training now...")
            await ensemble_service.train_for_vehicle(target_arac_id)

        new_preds = []
        for s in sefer_list:
            # Predictor.predict synchronous olduğu için session gerektirmez
            # Ancak girdi verilerini hazırlamamız lazım
            sefer_dict = {
                "mesafe_km": s.mesafe_km,
                "ton": float(s.net_kg or 0) / 1000.0,
                "ascent_m": s.ascent_m or 0,
                "descent_m": s.descent_m or 0,
                "zorluk": getattr(s, "zorluk", "Normal"),
                "rota_detay": s.rota_detay,
            }
            res = predictor.predict(sefer_dict)
            new_preds.append(res.tahmin_l_100km)

        # 4. Legacy Simulation (Pure Physics Baseline)
        legacy_preds = []
        for s in sefer_list:
            # Boş tüketim + tonaj etkisi basitleştirilmiş
            base = 18.0
            yuk_etkisi = (float(s.net_kg or 0) / 1000.0) * 0.4
            legacy_preds.append(base + yuk_etkisi)

    # Convert to L/100km if needed
    y_true_norm = []
    for i, s in enumerate(sefer_list):
        y_true_norm.append((y_true[i] / s.mesafe_km) * 100)

    # 📊 İstatistikler
    r2_new = r2_score(y_true_norm, new_preds)
    mae_new = mean_absolute_error(y_true_norm, new_preds)

    # Legacy comparison
    r2_old = r2_score(y_true_norm, legacy_preds)
    mae_old = mean_absolute_error(y_true_norm, legacy_preds)

    print(f"\nResults for Vehicle {target_arac_id}:")
    print("-" * 47)
    print(f"{'Metric':<15} | {'Legacy Baseline':<15} | {'Elite v2':<15}")
    print("-" * 47)
    print(f"{'R² Score':<15} | {r2_old:<15.3f} | {r2_new:<15.3f}")
    print(f"{'MAE (L/100km)':<15} | {mae_old:<15.2f} | {mae_new:<15.2f}")
    print("-" * 47)

    print("\n✅ DOĞRULUK ÖLÇÜMÜ TAMAMLANDI.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(compare_models_optimized())
