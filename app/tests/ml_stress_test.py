import os
import sys
import numpy as np
import threading
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.ml.ensemble_predictor import EnsembleFuelPredictor, EnsemblePredictorService, SecurityError
from app.core.ml.kalman_estimator import KalmanFuelEstimator, KalmanEstimatorService
from app.core.ml.benchmark import ABTestFramework

def test_security_tampering():
    print("\n--- [1] RCE Protection & Checksum Verification Test ---")
    predictor = EnsembleFuelPredictor()
    
    # Gerçek eğitim simülasyonu
    X = np.random.rand(20, 11)
    y = np.random.rand(20)
    predictor.gb_model.fit(X, y)
    predictor.rf_model.fit(X, y)
    if predictor.xgb_model:
        predictor.xgb_model.fit(X, y)
    if predictor.lgb_model:
        predictor.lgb_model.fit(X, y)
    
    predictor.is_trained = True
    test_path = "test_model_security"
    
    # 1. Normal Kaydet
    predictor.save_model(test_path)
    print("Model normal şekilde kaydedildi.")
    
    # 2. Dosyayı manuel boz (Tampering)
    sklearn_file = f"{test_path}_sklearn.joblib"
    with open(sklearn_file, "ab") as f:
        f.write(b"\x00\x00\x00") # Sona çöp veri ekle
    print("Model dosyası manipüle edildi (Tampered).")
    
    # 3. Yüklemeye çalış
    try:
        predictor.load_model(test_path)
        print("❌ HATA: Manipüle edilmiş dosya yüklenmemeliydi!")
    except SecurityError:
        print("✅ BAŞARILI: Checksum uyuşmazlığı tespit edildi ve yükleme reddedildi.")
    except Exception as e:
        print(f"✅ BAŞARILI: Beklendiği gibi hata alındı: {type(e).__name__}")
    finally:
        # Temizlik
        for p in Path(".").glob(f"{test_path}*"):
            p.unlink()

def test_memory_lru_eviction():
    print("\n--- [2] Memory Pressure & LRU Eviction Test ---")
    service = EnsemblePredictorService()
    service.MAX_PREDICTORS = 5 # Test için limiti düşür
    
    print(f"Limit: {service.MAX_PREDICTORS}")
    
    # Limiti aşacak kadar araç ekle
    for i in range(1, 8):
        service.get_predictor(i)
        print(f"Araç {i} eklendi. Mevcut cache boyutu: {len(service.predictors)}")
        
    print(f"Final Boyut: {len(service.predictors)}")
    if len(service.predictors) <= service.MAX_PREDICTORS:
        print(f"✅ BAŞARILI: LRU Cache limiti aşılmadı. Eski araçlar tahliye edildi.")
        if 1 not in service.predictors:
            print("✅ BAŞARILI: En eski araç (1) gerçekten tahliye edilmiş.")
    else:
        print("❌ HATA: LRU Cache limiti aşıldı!")

def test_kalman_stability_stress():
    print("\n--- [3] Kalman Filter 10.000 Iteration Stability Stress Test ---")
    estimator = KalmanFuelEstimator(1)
    
    # Sentetik veri üret
    np.random.seed(42)
    iterations = 10000
    
    print(f"{iterations} iterasyon başlıyor...")
    start_time = time.time()
    
    for i in range(iterations):
        features = {'ton': 25+np.random.normal(0, 5), 'ascent_m': 100+np.random.normal(0, 50), 'arac_yasi': 5}
        # Tüketim dalgalı ama ortalamada tutarlı
        observed = 32.0 + (features['ton']-25)*0.12 + np.random.normal(0, 2)
        
        estimator.update(features, observed)
        
        # Her 1000 iterasyonda bir P matrisinin simetrikliğini kontrol et
        if i % 1000 == 0:
            P = estimator.state.P
            is_symmetric = np.allclose(P, P.T, atol=1e-8)
            is_positive_definite = np.all(np.linalg.eigvals(P) > 0)
            if not (is_symmetric and is_positive_definite):
                print(f"❌ KRİTİK HATA: İterasyon {i}'de stabilite bozuldu!")
                return

    duration = time.time() - start_time
    print(f"✅ BAŞARILI: {iterations} iterasyon tamamlandı.")
    print(f"Süre: {duration:.2f} saniye. Ortalama: {duration/iterations*1000:.4f} ms/iter")
    print(f"Final Kovaryans Diagonali (P): {np.diag(estimator.state.P)}")
    print("Simetri ve Pozitif-Tanımlılık korundu.")

def test_statistical_selectivity():
    print("\n--- [4] Statistical Test Selectivity (Normal vs Non-Normal) ---")
    ab_test = ABTestFramework()
    
    # 1. Normal Dağılan Hatalar (T-Test beklenen)
    actuals = np.ones(100) * 30
    pred_a = 30 + np.random.normal(0, 1, 100)
    pred_b = 30 + np.random.normal(0, 1.2, 100)
    
    print("Senaryo 1: Normal Dağılım")
    result_normal = ab_test.run_ab_test("Normal_Test", "ModelA", pred_a, "ModelB", pred_b, actuals)
    print(f"Kullanılan Test: {result_normal.test_type}")
    
    # 2. Uç Değerli (Outlier) Dağılım (Wilcoxon beklenen)
    pred_a_out = 30 + np.random.normal(0, 1, 100)
    pred_a_out[0] = 500 # Devasa outlier
    pred_b_out = 30 + np.random.normal(0, 1, 100)
    
    print("\nSenaryo 2: Outlier (Non-Normal) Dağılım")
    result_outlier = ab_test.run_ab_test("Outlier_Test", "ModelA", pred_a_out, "ModelB", pred_b_out, actuals)
    print(f"Kullanılan Test: {result_outlier.test_type}")

if __name__ == "__main__":
    test_security_tampering()
    test_memory_lru_eviction()
    test_kalman_stability_stress()
    test_statistical_selectivity()
    print("\n--- TÜM STRES TESTLERİ TAMAMLANDI ---")
