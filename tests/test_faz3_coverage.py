import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
import shutil
import traceback

from app.core.ml.ensemble_predictor import EnsembleFuelPredictor, PredictionResult


class TestEnsembleFeatureEngineering:
    """Ensemble model öznitelik üretimi testleri."""

    def test_prepare_features_16_dimensions(self):
        """16 farklı özniteliğin üretildiğini ve boyutlarını doğrula."""
        predictor = EnsembleFuelPredictor()

        test_sefer = {
            "mesafe_km": 100.0,
            "ton": 20.0,
            "ascent_m": 500.0,
            "descent_m": 300.0,
            "flat_distance_km": 50.0,
            "zorluk": "Zor",
            "arac_yasi": 3,
            "yas_faktoru": 1.05,
            "mevsim_faktor": 1.1,
            "sofor_katsayi": 0.95,
            "rota_detay": {
                "route_analysis": {
                    "motorway": {"flat": 20, "up": 5, "down": 5},
                    "trunk": {"flat": 10, "up": 0, "down": 0},
                    "primary": {"flat": 10, "up": 0, "down": 0},
                    "residential": {"flat": 0, "up": 0, "down": 0},
                    "unclassified": {"flat": 0, "up": 0, "down": 0},
                }
            },
        }

        features = predictor.prepare_features([test_sefer])

        # Boyut kontrolü (1 sefer, 16 feature)
        assert features.shape == (1, 16)

        # Değer kontrolleri (mesafe_km çıktı, ton artık 0. index)
        f = features[0]
        assert f[0] == 20.0  # ton
        assert f[1] == 500.0  # ascent
        assert f[2] == 300.0  # descent
        assert f[3] == 200.0  # net_elevation (500-300)
        assert f[4] == 0.2  # yuk_yogunlugu (20/100)
        assert f[10] == 0.3  # motorway_ratio (30/100)
        assert f[15] == 50.0  # flat_km

    def test_prepare_features_minimal_data(self):
        """Minimum veri ile feature engineering hatasız çalışmalı."""
        predictor = EnsembleFuelPredictor()
        minimal_sefer = {"mesafe_km": 50}  # ton, ascent vb. eksik

        features = predictor.prepare_features([minimal_sefer])
        assert features.shape == (1, 16)
        assert features[0][0] == 0.0  # ton (index 0) default 0 olmalı


class TestEnsembleResilience:
    """Uç durum ve girdi toleransı testleri."""

    def test_predict_zero_distance_handling(self):
        predictor = EnsembleFuelPredictor()
        bad_sefer = {"mesafe_km": 0, "ton": 10}
        result = predictor.predict(bad_sefer)
        assert result.features_used["mesafe_km"] == 100

    def test_predict_none_values(self):
        predictor = EnsembleFuelPredictor()
        sefer_with_nones = {"mesafe_km": 100, "ton": None}
        result = predictor.predict(sefer_with_nones)
        assert result.tahmin_l_100km > 0


class TestEnsemblePersistence:
    """Model kaydetme ve yükleme testleri."""

    @pytest.fixture
    def test_models_dir(self):
        path = Path("tests/temp_models")
        path.mkdir(parents=True, exist_ok=True)
        yield path
        if path.exists():
            shutil.rmtree(path)

    def test_save_load_roundtrip(self, test_models_dir):
        predictor = EnsembleFuelPredictor()
        X_train = []
        y_train = []
        for i in range(15):
            X_train.append({"mesafe_km": 100 + i, "ton": 20})
            y_train.append(15.0 + (i * 0.1))

        predictor.fit(X_train, np.array(y_train))
        model_path = test_models_dir / "test_model_roundtrip.pkl"
        predictor.save_model(str(model_path))

        new_predictor = EnsembleFuelPredictor()
        new_predictor.load_model(str(model_path))

        assert new_predictor.is_trained

        test_sefer = {"mesafe_km": 120, "ton": 20}
        try:
            pred1 = predictor.predict(test_sefer)
            pred2 = new_predictor.predict(test_sefer)
            assert pred1.tahmin_l_100km == pred2.tahmin_l_100km
            assert "physics" in new_predictor.weights
        except Exception as e:
            print(f"\nPrediction failed after loading: {e}")
            traceback.print_exc()
            raise e


class TestPredictionServiceIntegration:
    """PredictionService ve Repository entegrasyonu (Mocked)."""

    @pytest.mark.asyncio
    async def test_predict_consumption_logic(self):
        from app.core.ml.ensemble_predictor import EnsemblePredictorService

        service = EnsemblePredictorService()
        service._arac_repo = AsyncMock()

        arac_data = {
            "id": 99,
            "plaka": "34 TEST 99",
            "marka": "Mercedes",
            "yil": 2022,
            "kapasite_ton": 25.0,
            "euro_sinifi": "EURO6",
        }
        service._arac_repo.get_by_id.return_value = arac_data

        arac_id = 99
        mock_predictor = MagicMock(spec=EnsembleFuelPredictor)
        mock_predictor.is_trained = True
        mock_predictor.predict.return_value = PredictionResult(
            tahmin_l_100km=32.0,
            physics_only=30.0,
            ml_correction=2.0,
            confidence_low=31.0,
            confidence_high=33.0,
            physics_weight=0.2,
            features_used={},
        )
        service.predictors[arac_id] = mock_predictor

        result = await service.predict_consumption(
            arac_id=arac_id, mesafe_km=500.0, ton=25.0
        )

        assert result["success"]
        assert result["tahmin_l_100km"] == 32.0
        assert result["tahmin_litre"] == 160.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
