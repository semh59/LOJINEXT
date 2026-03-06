"""
Faz 1 Kritik Bug Düzeltmeleri - Test Suite
BUG-1: Feature importance isim uyuşmazlığı (17 vs 10)
BUG-2: Docstring vs gerçek ağırlık farkı
BUG-3: tahmini_tuketim birim belirsizliği
BUG-4: model_used 'ensemble' eksikliği

Test Piramidi: %70 Unit Tests
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Project root
sys.path.insert(0, str(Path(__file__).parent.parent))


# ===============================================================
# BUG-1: Feature Importance İsim Senkronizasyonu
# ===============================================================
class TestBug1FeatureImportanceSync:
    """
    EnsembleFuelPredictor.FEATURE_NAMES (17 isim) ile
    fit() içinde kullanılan feature_names listesi senkron olmalı.
    """

    def test_feature_names_count_is_17(self):
        """FEATURE_NAMES'in tam 17 özellik içerdiğini doğrula"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()
        assert len(predictor.FEATURE_NAMES) == 17, (
            f"FEATURE_NAMES {len(predictor.FEATURE_NAMES)} eleman içeriyor, 17 olmalı"
        )

    def test_feature_names_contains_expected_fields(self):
        """Kritik feature'ların FEATURE_NAMES içinde olduğunu doğrula"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()
        expected_features = [
            "mesafe_km",
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
        for feature in expected_features:
            assert feature in predictor.FEATURE_NAMES, (
                f"'{feature}' FEATURE_NAMES'de bulunamadı"
            )

    def test_prepare_features_output_shape_matches_feature_names(self):
        """prepare_features() çıktısının FEATURE_NAMES ile aynı boyutta olduğunu doğrula"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()

        sample_sefer = {
            "mesafe_km": 500,
            "ton": 20,
            "ascent_m": 300,
            "descent_m": 200,
            "flat_distance_km": 100,
            "zorluk": "Normal",
            "arac_yasi": 3,
            "yas_faktoru": 1.0,
            "mevsim_faktor": 1.05,
            "sofor_katsayi": 0.95,
        }

        features = predictor.prepare_features([sample_sefer])
        assert features.shape[1] == len(predictor.FEATURE_NAMES), (
            f"Feature matrix {features.shape[1]} sütun, "
            f"FEATURE_NAMES {len(predictor.FEATURE_NAMES)} eleman. Uyuşmuyor!"
        )

    def test_feature_importance_zip_uses_all_names(self):
        """
        fit() sonrası feature_importance dict'inde tüm 17 feature'ın
        bulunduğunu doğrula — BUG-1'in asıl regresyon testi.
        """
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()

        # Minimum 10 sefer üret (fit gerekliliği)
        seferler = []
        np.random.seed(42)
        for _ in range(15):
            seferler.append(
                {
                    "mesafe_km": float(np.random.uniform(200, 800)),
                    "ton": float(np.random.uniform(5, 25)),
                    "ascent_m": float(np.random.uniform(0, 500)),
                    "descent_m": float(np.random.uniform(0, 400)),
                    "flat_distance_km": float(np.random.uniform(50, 300)),
                    "zorluk": "Normal",
                    "arac_yasi": float(np.random.randint(1, 10)),
                    "yas_faktoru": 1.0,
                    "mevsim_faktor": 1.0,
                    "sofor_katsayi": 1.0,
                }
            )

        # Gerçekçi yakıt değerleri oluştur (litre, L/100km değil)
        y_actual = np.array([s["mesafe_km"] * 0.32 + s["ton"] * 0.5 for s in seferler])

        result = predictor.fit(seferler, y_actual)
        assert result["success"] is True, f"Eğitim başarısız: {result.get('error')}"

        feat_imp = result.get("feature_importance", {})
        assert len(feat_imp) == 17, (
            f"Feature importance {len(feat_imp)} anahtar içeriyor, 17 olmalı. "
            f"Mevcut anahtarlar: {list(feat_imp.keys())}"
        )

        # Tüm FEATURE_NAMES anahtarlarının mevcut olduğunu doğrula
        for name in predictor.FEATURE_NAMES:
            assert name in feat_imp, f"Feature importance'da '{name}' eksik"


# ===============================================================
# BUG-2: Docstring vs Gerçek Ağırlık Tutarlılığı
# ===============================================================
class TestBug2WeightsConsistency:
    """
    WEIGHTS dict'inin toplam ağırlığı 1.0 olmalı ve
    5 model tanımlı olmalı.
    """

    def test_weights_sum_to_one(self):
        """Tüm model ağırlıklarının toplamı 1.0 olmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        weights = EnsembleFuelPredictor.WEIGHTS
        total = sum(weights.values())
        assert total == pytest.approx(1.0, abs=1e-6), (
            f"Ağırlıklar toplamı {total}, 1.0 olmalı"
        )

    def test_five_models_defined(self):
        """WEIGHTS dict'inde tam 5 model tanımlı olmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        weights = EnsembleFuelPredictor.WEIGHTS
        expected_models = {"physics", "lightgbm", "xgboost", "gb", "rf"}
        assert set(weights.keys()) == expected_models, (
            f"Tanımlı modeller: {set(weights.keys())}, beklenen: {expected_models}"
        )

    def test_xgboost_is_dominant(self):
        """XGBoost en yüksek ağırlığa sahip olmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        weights = EnsembleFuelPredictor.WEIGHTS
        max_model = max(weights, key=weights.get)
        assert max_model == "xgboost", (
            f"En yüksek ağırlıklı model {max_model}, xgboost olmalı"
        )

    def test_no_zero_weights(self):
        """Hiçbir modelin ağırlığı 0 olmamalı (deaktif model olmamalı)"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        weights = EnsembleFuelPredictor.WEIGHTS
        for model, weight in weights.items():
            assert weight > 0, (
                f"'{model}' model ağırlığı {weight}, sıfırdan büyük olmalı"
            )

    def test_docstring_matches_weights(self):
        """Docstring'deki model ve ağırlık bilgileri gerçek WEIGHTS ile tutarlı olmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        docstring = EnsembleFuelPredictor.__doc__
        assert "5 Model" in docstring, "Docstring '5 Model' içermeli"
        assert "LightGBM" in docstring, "Docstring 'LightGBM' içermeli"

        # Ağırlıkların docstring'de doğru gösterildiğini kontrol et
        weights = EnsembleFuelPredictor.WEIGHTS
        for model, weight in weights.items():
            percent = int(weight * 100)
            assert (
                str(percent) in docstring
                or f"%{percent}" in docstring
                or f"(%{percent})" in docstring
            ), f"Model '{model}' ağırlığı %{percent} docstring'de bulunamadı"


# ===============================================================
# BUG-3: Birim Belirsizliği (tahmini_tuketim)
# ===============================================================
class TestBug3UnitClarification:
    """
    PredictionResponse schema'sının birim netliğini doğrula:
    - tahmini_tuketim: L/100km
    - tahmini_litre: toplam litre
    """

    def test_schema_has_both_unit_fields(self):
        """PredictionResponse hem L/100km hem toplam litre alanına sahip olmalı"""
        from app.schemas.prediction import PredictionResponse

        fields = PredictionResponse.model_fields
        assert "tahmini_tuketim" in fields, "tahmini_tuketim alanı eksik"
        assert "tahmini_litre" in fields, "tahmini_litre alanı eksik"

    def test_tahmini_tuketim_description_says_l_100km(self):
        """tahmini_tuketim alanının açıklaması L/100km ifade etmeli"""
        from app.schemas.prediction import PredictionResponse

        desc = PredictionResponse.model_fields["tahmini_tuketim"].description
        assert "L/100km" in desc, (
            f"tahmini_tuketim açıklaması '{desc}', 'L/100km' içermeli"
        )

    def test_tahmini_litre_description_says_litre(self):
        """tahmini_litre alanının açıklaması 'litre' ifade etmeli"""
        from app.schemas.prediction import PredictionResponse

        desc = PredictionResponse.model_fields["tahmini_litre"].description
        assert "litre" in desc.lower(), (
            f"tahmini_litre açıklaması '{desc}', 'litre' içermeli"
        )

    def test_response_serialization_with_both_values(self):
        """Her iki birim de JSON'da doğru serileştirilmeli"""
        from app.schemas.prediction import PredictionResponse

        response = PredictionResponse(
            tahmini_tuketim=32.5,
            tahmini_litre=162.5,
            model_used="ensemble",
            confidence_low=29.0,
            confidence_high=36.0,
        )
        data = response.model_dump()
        assert data["tahmini_tuketim"] == 32.5
        assert data["tahmini_litre"] == 162.5

    def test_tahmini_litre_is_optional(self):
        """tahmini_litre opsiyonel olmalı (geriye uyumluluk)"""
        from app.schemas.prediction import PredictionResponse

        # tahmini_litre olmadan da oluşturulabilmeli
        response = PredictionResponse(
            tahmini_tuketim=32.5,
            model_used="ensemble",
        )
        assert response.tahmini_litre is None

    def test_confidence_descriptions_include_unit(self):
        """Güven aralığı alanları da birim belirtmeli"""
        from app.schemas.prediction import PredictionResponse

        low_desc = PredictionResponse.model_fields["confidence_low"].description
        high_desc = PredictionResponse.model_fields["confidence_high"].description
        assert "L/100km" in low_desc, (
            f"confidence_low açıklaması birim içermeli, mevcut: '{low_desc}'"
        )
        assert "L/100km" in high_desc, (
            f"confidence_high açıklaması birim içermeli, mevcut: '{high_desc}'"
        )

    def test_prediction_request_default_model_is_ensemble(self):
        """PredictionRequest varsayılan model tipi 'ensemble' olmalı"""
        from app.schemas.prediction import PredictionRequest

        default = PredictionRequest.model_fields["model_type"].default
        assert default == "ensemble", (
            f"Varsayılan model tipi '{default}', 'ensemble' olmalı"
        )


# ===============================================================
# BUG-4: model_used 'ensemble' Desteği
# ===============================================================
class TestBug4ModelUsedEnsemble:
    """
    model_used Literal tipi 'ensemble' değerini desteklemeli.
    """

    def test_model_used_accepts_ensemble(self):
        """PredictionResponse model_used='ensemble' kabul etmeli"""
        from app.schemas.prediction import PredictionResponse

        response = PredictionResponse(
            tahmini_tuketim=32.5,
            model_used="ensemble",
        )
        assert response.model_used == "ensemble"

    def test_model_used_accepts_linear(self):
        """PredictionResponse model_used='linear' hala çalışmalı (backward compat)"""
        from app.schemas.prediction import PredictionResponse

        response = PredictionResponse(
            tahmini_tuketim=25.0,
            model_used="linear",
        )
        assert response.model_used == "linear"

    def test_model_used_accepts_xgboost(self):
        """PredictionResponse model_used='xgboost' hala çalışmalı (backward compat)"""
        from app.schemas.prediction import PredictionResponse

        response = PredictionResponse(
            tahmini_tuketim=30.0,
            model_used="xgboost",
        )
        assert response.model_used == "xgboost"

    def test_model_used_rejects_invalid(self):
        """Geçersiz model_used değeri reddedilmeli"""
        from pydantic import ValidationError

        from app.schemas.prediction import PredictionResponse

        with pytest.raises(ValidationError):
            PredictionResponse(
                tahmini_tuketim=30.0,
                model_used="invalid_model",  # type: ignore
            )

    def test_prediction_request_model_type_accepts_ensemble(self):
        """PredictionRequest model_type='ensemble' kabul etmeli"""
        from app.schemas.prediction import PredictionRequest

        request = PredictionRequest(
            arac_id=1,
            mesafe_km=500,
            model_type="ensemble",
        )
        assert request.model_type == "ensemble"


# ===============================================================
# INTEGRATION: Ensemble Predict → Feature Count Consistency
# ===============================================================
class TestEnsemblePredictIntegration:
    """
    EnsembleFuelPredictor.predict() fonksiyonunun
    temel senaryo ve edge case'lerde doğru çalıştığını doğrular.
    """

    def test_predict_without_training_returns_physics_only(self):
        """Eğitimsiz modelde physics-only sonuç dönmeli"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()

        result = predictor.predict(
            {"mesafe_km": 500, "ton": 20, "ascent_m": 200, "descent_m": 100}
        )

        assert result.physics_weight == 1.0, (
            "Eğitimsiz modelde physics_weight 1.0 olmalı"
        )
        assert result.ml_correction == 0.0, "Eğitimsiz modelde ML düzeltme 0 olmalı"
        assert result.tahmin_l_100km > 0, "Tahmin pozitif olmalı"

    def test_predict_with_zero_distance_uses_default(self):
        """Sıfır mesafe durumunda varsayılan 100km kullanılmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()
        result = predictor.predict({"mesafe_km": 0, "ton": 10})

        assert result.tahmin_l_100km > 0, "Sıfır mesafe için de tahmin üretilmeli"

    def test_predict_with_missing_fields_uses_defaults(self):
        """Eksik alanlar varsayılan değerlerle doldurulmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()
        result = predictor.predict({"mesafe_km": 300})  # Minimal input

        assert result.tahmin_l_100km > 0, "Minimal girdiyle de tahmin üretilmeli"

    @pytest.mark.parametrize(
        "mesafe,ton,expected_range",
        [
            (500, 20, (20.0, 50.0)),  # TIR normal yüklü: ~30 L/100km
            (500, 0, (15.0, 45.0)),  # Boş TIR: daha düşük
            (1000, 25, (20.0, 55.0)),  # Uzun mesafe yüklü
        ],
    )
    def test_predict_realistic_ranges(self, mesafe, ton, expected_range):
        """Tahmin sonuçları gerçekçi TIR aralığında olmalı"""
        from app.core.ml.ensemble_predictor import EnsembleFuelPredictor

        predictor = EnsembleFuelPredictor()
        result = predictor.predict({"mesafe_km": mesafe, "ton": ton})

        assert expected_range[0] <= result.tahmin_l_100km <= expected_range[1], (
            f"Tahmin {result.tahmin_l_100km} L/100km, beklenen aralık: {expected_range}"
        )


# ===============================================================
# PHYSICS MODEL: Temel Doğruluk Testleri
# ===============================================================
class TestPhysicsModelBasic:
    """Fizik modelinin temel doğruluğu ve tutarlılığı."""

    def test_heavier_load_more_fuel(self):
        """Daha ağır yük → daha fazla yakıt"""
        from app.core.ml.physics_fuel_predictor import (
            PhysicsBasedFuelPredictor,
            RouteConditions,
        )

        predictor = PhysicsBasedFuelPredictor()
        light = predictor.predict(RouteConditions(distance_km=500, load_ton=5))
        heavy = predictor.predict(RouteConditions(distance_km=500, load_ton=25))

        assert heavy.total_liters > light.total_liters, (
            f"25 ton ({heavy.total_liters}L) > 5 ton ({light.total_liters}L) olmalı"
        )

    def test_more_ascent_more_fuel(self):
        """Daha fazla tırmanış → daha fazla yakıt"""
        from app.core.ml.physics_fuel_predictor import (
            PhysicsBasedFuelPredictor,
            RouteConditions,
        )

        predictor = PhysicsBasedFuelPredictor()
        flat = predictor.predict(
            RouteConditions(distance_km=500, load_ton=15, ascent_m=0)
        )
        hilly = predictor.predict(
            RouteConditions(distance_km=500, load_ton=15, ascent_m=1000)
        )

        assert hilly.total_liters > flat.total_liters, (
            f"1000m tırmanış ({hilly.total_liters}L) > düz yol ({flat.total_liters}L) olmalı"
        )

    def test_empty_trip_less_fuel(self):
        """Boş sefer → daha az yakıt"""
        from app.core.ml.physics_fuel_predictor import (
            PhysicsBasedFuelPredictor,
            RouteConditions,
        )

        predictor = PhysicsBasedFuelPredictor()
        loaded = predictor.predict(
            RouteConditions(distance_km=500, load_ton=20, is_empty_trip=False)
        )
        empty = predictor.predict(
            RouteConditions(distance_km=500, load_ton=20, is_empty_trip=True)
        )

        assert empty.total_liters < loaded.total_liters, (
            f"Boş sefer ({empty.total_liters}L) < yüklü ({loaded.total_liters}L) olmalı"
        )

    def test_zero_distance_returns_zero(self):
        """Sıfır mesafe → sıfır tüketim"""
        from app.core.ml.physics_fuel_predictor import (
            PhysicsBasedFuelPredictor,
            RouteConditions,
        )

        predictor = PhysicsBasedFuelPredictor()
        result = predictor.predict(RouteConditions(distance_km=0, load_ton=20))
        assert result.consumption_l_100km == 0.0
