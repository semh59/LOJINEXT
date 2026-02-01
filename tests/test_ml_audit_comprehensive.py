"""
ML Katmanı Kapsamlı Audit Test Suite
Paranoyak seviye denetim için güvenlik, stabilite ve edge case testleri.
"""

import pytest
import numpy as np
import threading
import time
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, '.')


class TestSingletonThreadSafety:
    """Singleton fonksiyonlarının thread-safety testleri"""
    
    def test_kalman_service_thread_safety(self):
        """Kalman service eşzamanlı erişimde tek instance döndürmeli"""
        from app.core.ml.kalman_estimator import get_kalman_service, KalmanEstimatorService
        
        results = []
        errors = []
        
        def get_service():
            try:
                service = get_kalman_service()
                results.append(id(service))
            except Exception as e:
                errors.append(str(e))
        
        # 10 thread ile eşzamanlı erişim
        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread hatası: {errors}"
        # Tüm thread'ler aynı instance'ı almalı
        assert len(set(results)) == 1, "Farklı singleton instance'ları oluştu!"
    
    def test_ensemble_service_thread_safety(self):
        """Ensemble service eşzamanlı erişimde tek instance döndürmeli"""
        from app.core.ml.ensemble_predictor import get_ensemble_service
        
        results = []
        
        def get_service():
            service = get_ensemble_service()
            results.append(id(service))
        
        threads = [threading.Thread(target=get_service) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(set(results)) == 1, "Farklı singleton instance'ları oluştu!"


class TestNumericalEdgeCases:
    """Sayısal edge case testleri - NaN, Inf, sıfır, negatif değerler"""
    
    def test_physics_predictor_zero_distance(self):
        """Sıfır mesafe ile tahmin crash etmemeli"""
        from app.core.ml.physics_fuel_predictor import (
            PhysicsBasedFuelPredictor, RouteConditions
        )
        
        predictor = PhysicsBasedFuelPredictor()
        route = RouteConditions(
            distance_km=0,  # Zero distance
            load_ton=20,
            ascent_m=100
        )
        
        result = predictor.predict(route)
        assert result.consumption_l_100km == 0.0  # Division handled
        assert not np.isnan(result.total_liters)
        assert not np.isinf(result.total_liters)
    
    def test_physics_predictor_zero_load(self):
        """Sıfır yük ile tahmin çalışmalı"""
        from app.core.ml.physics_fuel_predictor import (
            PhysicsBasedFuelPredictor, RouteConditions
        )
        
        predictor = PhysicsBasedFuelPredictor()
        route = RouteConditions(
            distance_km=100,
            load_ton=0,  # Zero load
            ascent_m=100
        )
        
        result = predictor.predict(route)
        assert result.total_liters > 0
        assert not np.isnan(result.consumption_l_100km)
    
    def test_physics_calibrate_zero_predictions(self):
        """Sıfır tahminlerle kalibrasyon crash etmemeli"""
        from app.core.ml.physics_fuel_predictor import PhysicsBasedFuelPredictor
        
        predictor = PhysicsBasedFuelPredictor()
        predictions = [0.0, 0.0, 0.0, 0.0, 0.0]  # Zero predictions
        actuals = [10.0, 12.0, 11.0, 10.5, 11.5]
        
        result = predictor.calibrate_with_historical(predictions, actuals)
        assert 'calibration_factor' in result
        assert not np.isnan(result['calibration_factor'])
        assert not np.isinf(result['calibration_factor'])
    
    def test_hybrid_predictor_zero_prediction(self):
        """learn_from_actual sıfır prediction ile crash etmemeli"""
        from app.core.ml.physics_fuel_predictor import HybridFuelPredictor
        
        predictor = HybridFuelPredictor()
        
        # Zero prediction ile öğrenme
        predictor.learn_from_actual(0.0, 10.0)
        
        assert not np.isnan(predictor.correction_factor)
        assert not np.isinf(predictor.correction_factor)
    
    def test_fuel_predictor_constant_features(self):
        """Sabit feature değerlerinde (std=0) crash olmamalı"""
        from app.core.ml.fuel_predictor import LinearRegressionModel
        
        model = LinearRegressionModel()
        
        # Tüm özellikler sabit
        X = np.array([
            [100, 20],
            [100, 20],
            [100, 20],
            [100, 20],
        ])
        y = np.array([30.0, 31.0, 29.0, 30.5])
        
        result = model.fit(X, y)
        assert result['success'] == True
        
        # Tahmin yapabilmeli
        pred, _ = model.predict(X[:1])
        assert not np.isnan(pred[0])
    
    def test_driver_performance_zero_consumption(self):
        """Sıfır ortalama tüketim ile tutarlılık hesabı crash etmemeli"""
        from app.core.ml.driver_performance_ml import DriverPerformanceML
        
        ml = DriverPerformanceML()
        
        stats = [{
            'toplam_sefer': 10,
            'toplam_km': 1000,
            'ort_tuketim': 0.0,  # Zero consumption
            'filo_karsilastirma': 0,
            'en_iyi_tuketim': 0.0,
            'en_kotu_tuketim': 0.0,
            'trend': 'stable',
            'guzergah_sayisi': 1,
            'bos_sefer_sayisi': 0,
            'toplam_ton': 100
        }]
        
        features = ml.prepare_features(stats)
        
        # NaN veya Inf olmamalı
        assert not np.any(np.isnan(features))
        assert not np.any(np.isinf(features))


class TestKalmanStability:
    """Kalman filtre stabilite ve güvenlik testleri"""
    
    def test_covariance_remains_positive_definite(self):
        """Covariance matris birçok güncelleme sonrası pozitif tanımlı kalmalı"""
        from app.core.ml.kalman_estimator import KalmanFuelEstimator
        
        kf = KalmanFuelEstimator()
        
        # 100 güncelleme yap
        for i in range(100):
            kf.update({'ton': 15 + i % 10}, 30 + np.random.normal(0, 2))
        
        # Diagonal elemanları pozitif kalmalı
        assert np.all(np.diag(kf.state.P) > 0), "Covariance diagonal negatif!"
        
        # Simetrik kalmalı
        assert np.allclose(kf.state.P, kf.state.P.T), "Covariance simetrik değil!"
    
    def test_batch_update_limit(self):
        """Batch update MAX_BATCH_SIZE limitini aşınca hata vermeli"""
        from app.core.ml.kalman_estimator import KalmanFuelEstimator
        
        kf = KalmanFuelEstimator()
        
        # MAX_BATCH_SIZE'dan fazla gözlem
        large_batch = [
            {'features': {'ton': 10}, 'consumption': 30.0}
            for _ in range(1001)
        ]
        
        with pytest.raises(ValueError, match="Batch boyutu"):
            kf.batch_update(large_batch)
    
    def test_underflow_protection(self):
        """Çok küçük covariance değerlerinde underflow koruması"""
        from app.core.ml.kalman_estimator import KalmanFuelEstimator
        
        kf = KalmanFuelEstimator()
        
        # Covariance'ı çok küçük yap
        kf.state.P = np.eye(4) * 1e-15
        kf.R = 1e-15
        
        # Update crash etmemeli
        kf.update({'ton': 10}, 30.0)
        
        # P değerleri hala pozitif olmalı (fading memory + Q sayesinde)
        assert np.all(np.diag(kf.state.P) > 0)
    
    def test_outlier_observation(self):
        """Aykırı (10x normal) gözlem ile stabilite"""
        from app.core.ml.kalman_estimator import KalmanFuelEstimator
        
        kf = KalmanFuelEstimator()
        
        # Normal gözlemler
        for _ in range(10):
            kf.update({'ton': 15}, 32.0)
        
        state_before = kf.state.state.copy()
        
        # Aykırı gözlem (10x normal)
        kf.update({'ton': 15}, 320.0)  # 10x
        
        # State çok fazla değişmemeli (Kalman gain koruması)
        state_diff = np.abs(kf.state.state - state_before)
        assert np.all(state_diff < 50), "Aykırı gözlem state'i çok değiştirdi!"
    
    def test_load_state_validation_missing_fields(self):
        """load_state eksik alanlarla hata vermeli"""
        from app.core.ml.kalman_estimator import KalmanFuelEstimator
        
        kf = KalmanFuelEstimator()
        
        with pytest.raises(ValueError, match="zorunludur"):
            kf.load_state({'state': [1, 2, 3, 4]})  # P eksik
    
    def test_load_state_validation_wrong_shape(self):
        """load_state yanlış boyut ile hata vermeli"""
        from app.core.ml.kalman_estimator import KalmanFuelEstimator
        
        kf = KalmanFuelEstimator()
        
        with pytest.raises(ValueError, match="\\(4,\\)"):
            kf.load_state({
                'state': [1, 2, 3],  # 3 eleman (yanlış)
                'P': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
            })
    
    def test_load_state_validation_nan_values(self):
        """load_state NaN değerlerle hata vermeli"""
        from app.core.ml.kalman_estimator import KalmanFuelEstimator
        
        kf = KalmanFuelEstimator()
        
        with pytest.raises(ValueError, match="NaN/Inf"):
            kf.load_state({
                'state': [1, float('nan'), 3, 4],
                'P': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
            })


class TestEnsembleModel:
    """Ensemble model testleri"""
    
    def test_weights_sum_to_one(self):
        """Model ağırlıkları toplamı 1.0 olmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
        
        predictor = EnsembleFuelPredictor()
        total = sum(predictor.WEIGHTS.values())
        
        assert abs(total - 1.0) < 1e-9, f"Ağırlıklar toplamı 1.0 değil: {total}"
    
    def test_lru_cache_eviction_under_limit(self):
        """LRU cache limiti altında eviction olmamalı"""
        from app.core.ml.ensemble_predictor import EnsemblePredictorService
        
        service = EnsemblePredictorService()
        original_max = service.MAX_PREDICTORS
        service.MAX_PREDICTORS = 5
        
        try:
            # 5 predictor oluştur (limit dahilinde)
            for i in range(5):
                service.get_predictor(i)
            
            assert len(service.predictors) == 5
            assert all(i in service.predictors for i in range(5))
        finally:
            service.MAX_PREDICTORS = original_max
    
    def test_lru_cache_eviction_over_limit(self):
        """LRU cache limiti aşılınca en eski evict edilmeli"""
        from app.core.ml.ensemble_predictor import EnsemblePredictorService
        
        service = EnsemblePredictorService()
        original_max = service.MAX_PREDICTORS
        service.MAX_PREDICTORS = 3
        
        try:
            # 4 predictor oluştur (limit: 3)
            for i in range(4):
                service.get_predictor(i)
            
            # En eski (0) evict edilmiş olmalı
            assert 0 not in service.predictors
            assert 1 in service.predictors
            assert 2 in service.predictors
            assert 3 in service.predictors
        finally:
            service.MAX_PREDICTORS = original_max
    
    def test_untrained_model_fallback(self):
        """Eğitilmemiş model physics-only fallback yapmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
        
        predictor = EnsembleFuelPredictor()
        assert predictor.is_trained == False
        
        sefer = {
            'mesafe_km': 500,
            'ton': 20,
            'ascent_m': 1000,
            'descent_m': 800
        }
        
        result = predictor.predict(sefer)
        
        # Physics weight 1.0 olmalı (fallback)
        assert result.physics_weight == 1.0
        assert result.ml_correction == 0.0
    
    def test_prediction_determinism(self):
        """Aynı input için aynı output (determinism testi)"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
        
        predictor = EnsembleFuelPredictor()
        
        sefer = {
            'mesafe_km': 500,
            'ton': 20,
            'ascent_m': 1000,
            'descent_m': 800
        }
        
        # 10 prediction yap
        results = [predictor.predict(sefer).tahmin_l_100km for _ in range(10)]
        
        # Tüm sonuçlar aynı olmalı (deterministic)
        assert len(set(results)) == 1, f"Non-deterministic predictions: {results}"


class TestModelSerializationSecurity:
    """Model serialization güvenlik testleri"""
    
    def test_no_unsafe_pickle_in_ml_code(self):
        """ML kodunda güvensiz pickle.load kullanılmamalı"""
        ml_dir = Path(__file__).parent.parent / "app" / "core" / "ml"
        
        for file in ml_dir.glob("*.py"):
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()
                
                for i, line in enumerate(lines, 1):
                    # Comment veya string değilse
                    stripped = line.strip()
                    if stripped.startswith(("#", '"', "'")):
                        continue
                    
                    if "pickle.load" in line:
                        pytest.fail(
                            f"Güvensiz pickle.load bulundu: {file.name}:{i}"
                        )
    
    def test_torch_load_uses_weights_only(self):
        """torch.load weights_only=True kullanmalı"""
        ts_file = Path(__file__).parent.parent / "app" / "core" / "ml" / "time_series_predictor.py"
        
        if ts_file.exists():
            with open(ts_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "weights_only=True" in content, \
                    "time_series_predictor.py torch.load için weights_only=True kullanmalı"
    
    def test_checksum_function_exists(self):
        """Checksum hesaplama fonksiyonu mevcut olmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
        
        predictor = EnsembleFuelPredictor()
        assert hasattr(predictor, '_calculate_checksum')
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as tmp:
            tmp.write(b"test checksum data")
            tmp_path = tmp.name
        
        try:
            checksum = predictor._calculate_checksum(tmp_path)
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            os.unlink(tmp_path)


class TestBenchmarkStability:
    """Benchmark framework stabilite testleri"""
    
    def test_ab_test_zero_mae_handling(self):
        """MAE sıfır olduğunda improvement hesabı crash etmemeli"""
        from app.core.ml.benchmark import ABTestFramework
        
        ab = ABTestFramework()
        
        # Mükemmel tahminler (MAE = 0)
        actuals = np.array([10.0, 10.0, 10.0])
        perfect_a = np.array([10.0, 10.0, 10.0])
        perfect_b = np.array([10.0, 10.0, 10.0])
        
        result = ab.run_ab_test(
            "Perfect Models",
            "A", perfect_a,
            "B", perfect_b,
            actuals,
            metric='MAE'
        )
        
        # Crash olmamalı ve improvement 0 olmalı
        assert result.improvement_percent == 0.0
        assert not np.isnan(result.improvement_percent)
    
    def test_benchmark_nan_handling(self):
        """NaN içeren tahminler handle edilmeli"""
        from app.core.ml.benchmark import MLBenchmark
        
        benchmark = MLBenchmark()
        
        predictions = np.array([30.0, 31.0, np.nan, 29.0])
        actuals = np.array([30.0, 30.0, 30.0, 30.0])
        
        # NaN mask'lı metrikler hesaplanmalı veya güvenli şekilde handle edilmeli
        results = benchmark.benchmark_prediction_accuracy("NaN Model", predictions, actuals)
        
        # En azından bazı sonuçlar dönmeli
        assert len(results) > 0


class TestTimeSeries:
    """Time series predictor testleri"""
    
    def test_normalize_with_nan_and_inf(self):
        """Normalize NaN ve Inf değerlerle crash etmemeli"""
        from app.core.ml.time_series_predictor import TimeSeriesPredictor, TORCH_AVAILABLE
        
        if not TORCH_AVAILABLE:
            pytest.skip("PyTorch not available")
        
        predictor = TimeSeriesPredictor()
        
        X = np.array([
            [[1.0, 2.0, np.nan], [3.0, np.inf, 5.0]],
            [[6.0, 7.0, 8.0], [9.0, 10.0, 11.0]]
        ], dtype=np.float32)
        
        X_norm = predictor.normalize(X, fit=True)
        
        # NaN ve Inf temizlenmiş olmalı
        assert not np.any(np.isnan(X_norm))
        assert not np.any(np.isinf(X_norm))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
