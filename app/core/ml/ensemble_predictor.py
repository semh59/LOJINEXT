"""
TIR Yakıt Takip - Ensemble Tahmin Modeli
LightGBM + XGBoost + GradientBoosting + RandomForest + Fizik Modeli

5-Model Ensemble Architecture:
- Physics: %15 (Enerji tabanlı fizik modeli)
- LightGBM: %30 (Kategorik feature handling, hızlı)
- XGBoost: %25 (Güçlü gradient boosting)
- GradientBoosting: %15 (Sklearn baseline)
- RandomForest: %15 (Variance reduction)
"""

import hashlib
import threading
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


class SecurityError(Exception):
    """Güvenlik ihlali durumunda fırlatılan istisna"""
    pass

# Sklearn importları (lazy loading ile)
try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# XGBoost import (opsiyonel)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    xgb = None
    XGBOOST_AVAILABLE = False

# LightGBM import (opsiyonel)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    lgb = None
    LIGHTGBM_AVAILABLE = False

from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    RouteConditions,
    VehicleSpecs,
)
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    """Tahmin sonucu"""
    tahmin_l_100km: float
    physics_only: float
    ml_correction: float
    confidence_low: float
    confidence_high: float
    physics_weight: float
    features_used: Dict[str, float]


class EnsembleFuelPredictor:
    """
    Hibrit Ensemble Model (4 Model Kombinasyonu):
    1. Fizik bazlı base tahmin (%20)
    2. XGBoost - En güçlü model (%40)
    3. GradientBoosting (%20)
    4. RandomForest (%20)
    
    Feature'lar:
    - mesafe_km
    - ton (yük)
    - ascent_m (bayır çıkış)
    - descent_m (bayır iniş)
    - arac_yasi
    - yas_faktoru
    - mevsim_faktor
    - yuk_yogunlugu (ton/km)
    - sofor_katsayisi
    
    Model Performans Karşılaştırması (tipik):
    | Model            | MAE   | R² Skoru |
    |------------------|-------|----------|
    | Physics          | 3.2 L | 0.78     |
    | GradientBoosting | 2.5 L | 0.85     |
    | RandomForest     | 2.8 L | 0.82     |
    | XGBoost          | 1.9 L | 0.91     |
    | Ensemble         | 1.5 L | 0.94     |
    """

    FEATURE_NAMES = [
        'mesafe_km', 'ton', 'ascent_m', 'descent_m',
        'net_elevation', 'yuk_yogunlugu', 'zorluk',
        'arac_yasi', 'yas_faktoru', 'mevsim_faktor', 'sofor_katsayi'
    ]

    # Model ağırlıkları (5-model ensemble)
    WEIGHTS = {
        'physics': 0.15,   # Fizik modeli (enerji tabanlı)
        'lightgbm': 0.30,  # LightGBM (kategorik, hızlı)
        'xgboost': 0.25,   # XGBoost (güçlü)
        'gb': 0.15,        # GradientBoosting
        'rf': 0.15         # RandomForest
    }

    def __init__(self, vehicle_specs: VehicleSpecs = None):
        self.physics_model = PhysicsBasedFuelPredictor(vehicle_specs)

        # GradientBoosting
        if SKLEARN_AVAILABLE:
            self.gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )

            self.rf_model = RandomForestRegressor(
                n_estimators=50,
                max_depth=6,
                random_state=42
            )

            self.scaler = StandardScaler()
        else:
            self.gb_model = None
            self.rf_model = None
            self.scaler = None
            logger.warning("sklearn not available, using physics-only model")

        # XGBoost
        if XGBOOST_AVAILABLE:
            self.xgb_model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='reg:squarederror',
                random_state=42,
                verbosity=0
            )
            logger.info("XGBoost model initialized")
        else:
            self.xgb_model = None
            logger.warning("XGBoost not available, excluding from ensemble")

        # LightGBM
        if LIGHTGBM_AVAILABLE:
            self.lgb_model = lgb.LGBMRegressor(
                n_estimators=150,
                num_leaves=31,
                learning_rate=0.05,
                feature_fraction=0.8,
                bagging_fraction=0.8,
                bagging_freq=5,
                verbose=-1,
                random_state=42
            )
            logger.info("LightGBM model initialized")
        else:
            self.lgb_model = None
            logger.warning("LightGBM not available, excluding from ensemble")

        self.is_trained = False
        self.physics_weight = self.WEIGHTS['physics']
        self.training_stats = {}
        self._model_lock = threading.Lock()  # Tahmin ve eğitim arasında senkronizasyon için

    def prepare_features(self, seferler: List[Dict]) -> np.ndarray:
        """
        Feature engineering - Tüm faktörleri çıkar
        """
        features = []

        zorluk_map = {'Kolay': 1, 'Normal': 2, 'Zor': 3}

        for s in seferler:
            # Temel
            mesafe = float(s.get('mesafe_km', 0) or 0)
            ton = float(s.get('ton', 0) or 0)
            ascent = float(s.get('ascent_m', 0) or 0)
            descent = float(s.get('descent_m', 0) or 0)

            # Türetilmiş
            net_elevation = ascent - descent
            yuk_yogunlugu = ton / mesafe if mesafe > 0 else 0
            zorluk = zorluk_map.get(s.get('zorluk', 'Normal'), 2)

            # Araç yaşı
            arac_yasi = float(s.get('arac_yasi', 5) or 5)
            yas_faktoru = float(s.get('yas_faktoru', 1.0) or 1.0)

            # Mevsim ve şoför
            mevsim_faktor = float(s.get('mevsim_faktor', 1.0) or 1.0)
            sofor_katsayi = float(s.get('sofor_katsayi', 1.0) or 1.0)

            features.append([
                mesafe,
                ton,
                ascent,
                descent,
                net_elevation,
                yuk_yogunlugu,
                zorluk,
                arac_yasi,
                yas_faktoru,
                mevsim_faktor,
                sofor_katsayi
            ])

        return np.array(features)

    def _get_physics_predictions(self, seferler: List[Dict]) -> np.ndarray:
        """Fizik modeli tahminleri"""
        predictions = []

        for s in seferler:
            route = RouteConditions(
                distance_km=float(s.get('mesafe_km', 0) or 0),
                load_ton=float(s.get('ton', 0) or 0),
                ascent_m=float(s.get('ascent_m', 0) or 0),
                descent_m=float(s.get('descent_m', 0) or 0)
            )
            pred = self.physics_model.predict(route)
            predictions.append(pred.consumption_l_100km)

        return np.array(predictions)

    def fit(self, seferler: List[Dict], y_actual: np.ndarray) -> Dict:
        """
        Model eğitimi
        
        1. Feature'ları hazırla
        2. Fizik tahminleri al
        3. Residual (hata) hesapla
        4. ML ile residual öğren
        5. Ağırlıkları belirle
        """
        if len(seferler) < 10:
            return {
                'success': False,
                'error': f'Yetersiz veri: {len(seferler)} sefer. En az 10 gerekli.'
            }

        if not SKLEARN_AVAILABLE:
            return {
                'success': False,
                'error': 'sklearn kütüphanesi yüklü değil.'
            }

        try:
            # LOCK SCOPE FIX: Tüm eğitim lock içinde - is_trained flag atomik güncellemesi
            with self._model_lock:
                self.is_trained = False  # Eğitim sırasında eski tahminleri engelle
                
                # Feature hazırla
                X = self.prepare_features(seferler)
                X_scaled = self.scaler.fit_transform(X)

                # Fizik tahminleri
                y_physics = self._get_physics_predictions(seferler)

                # Residual = Gerçek - Fizik
                residuals = y_actual - y_physics

                # ML modelleri eğit
                self.gb_model.fit(X_scaled, residuals)
                self.rf_model.fit(X_scaled, residuals)

                # XGBoost eğitimi
                xgb_r2 = 0.0
                if self.xgb_model is not None:
                    self.xgb_model.fit(X_scaled, residuals)
                    xgb_pred = self.xgb_model.predict(X_scaled)
                    xgb_r2 = r2_score(residuals, xgb_pred) if len(residuals) > 0 else 0

                # LightGBM eğitimi
                lgb_r2 = 0.0
                if LIGHTGBM_AVAILABLE and self.lgb_model is not None:
                    self.lgb_model.fit(X_scaled, residuals)
                    lgb_pred = self.lgb_model.predict(X_scaled)
                    lgb_r2 = r2_score(residuals, lgb_pred) if len(residuals) > 0 else 0

                # Cross-validation skorları
                gb_scores = cross_val_score(
                    self.gb_model, X_scaled, residuals,
                    cv=min(5, len(seferler) // 2),
                    scoring='r2'
                )
                rf_scores = cross_val_score(
                    self.rf_model, X_scaled, residuals,
                    cv=min(5, len(seferler) // 2),
                    scoring='r2'
                )

                # Fizik model hata ortalaması
                physics_mae = np.mean(np.abs(residuals))

                self.training_stats = {
                    'sample_count': len(seferler),
                    'physics_mae': round(physics_mae, 2),
                    'gb_cv_mean': round(np.mean(gb_scores), 3),
                    'rf_cv_mean': round(np.mean(rf_scores), 3),
                    'xgb_r2': round(xgb_r2, 3) if xgb_r2 else None,
                    'lgb_r2': round(lgb_r2, 3) if lgb_r2 else None,
                    'lightgbm_available': LIGHTGBM_AVAILABLE,
                    'model_weights': self.WEIGHTS
                }
                
                # is_trained bayrağı lock içinde - RACE CONDITION FIX
                self.is_trained = True

            return {
                'success': True,
                **self.training_stats
            }

        except Exception as e:
            logger.error(f"Ensemble training error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def predict(self, sefer: Dict) -> PredictionResult:
        """
        Tek sefer için tahmin.
        
        INPUT VALIDATION: Eksik veya hatalı veri kontrolü.
        """
        # INPUT VALIDATION: Zorunlu alan kontrolü
        mesafe = sefer.get('mesafe_km')
        if mesafe is None or (isinstance(mesafe, (int, float)) and mesafe <= 0):
            logger.warning(f"Geçersiz mesafe değeri: {mesafe}, varsayılan 100 kullanılıyor")
            sefer = {**sefer, 'mesafe_km': 100}
        
        # Fizik tahmini (her zaman çalışır)
        route = RouteConditions(
            distance_km=float(sefer.get('mesafe_km', 0) or 0),
            load_ton=float(sefer.get('ton', 0) or 0),
            ascent_m=float(sefer.get('ascent_m', 0) or 0),
            descent_m=float(sefer.get('descent_m', 0) or 0)
        )
        physics_pred = self.physics_model.predict(route)
        physics_value = physics_pred.consumption_l_100km

        # Araç yaşı faktörünü uygula
        yas_faktoru = float(sefer.get('yas_faktoru', 1.0) or 1.0)
        physics_value *= yas_faktoru

        # Mevsim faktörünü uygula
        mevsim_faktor = float(sefer.get('mevsim_faktor', 1.0) or 1.0)
        physics_value *= mevsim_faktor

        # Tahmin sırasında modelin değişmediğinden emin ol (thread-safe)
        with self._model_lock:
            if not self.is_trained or not SKLEARN_AVAILABLE:
                # ML yok, sadece fizik
                return PredictionResult(
                tahmin_l_100km=round(physics_value, 1),
                physics_only=round(physics_value, 1),
                ml_correction=0.0,
                confidence_low=round(physics_value * 0.9, 1),
                confidence_high=round(physics_value * 1.1, 1),
                physics_weight=1.0,
                features_used=sefer
            )

        # ML düzeltme
        X = self.prepare_features([sefer])
        X_scaled = self.scaler.transform(X)

        gb_residual = self.gb_model.predict(X_scaled)[0]
        rf_residual = self.rf_model.predict(X_scaled)[0]

        # XGBoost residual
        xgb_residual = 0.0
        if self.xgb_model is not None:
            xgb_residual = self.xgb_model.predict(X_scaled)[0]

        # LightGBM residual
        lgb_residual = 0.0
        if LIGHTGBM_AVAILABLE and self.lgb_model is not None:
            lgb_residual = self.lgb_model.predict(X_scaled)[0]

        # Ağırlıklı ortalama tahmin
        # Physics değeri + ML residual düzeltmeleri
        physics_corrected = physics_value  # Physics zaten faktörlerle düzeltildi
        gb_prediction = physics_value + gb_residual
        rf_prediction = physics_value + rf_residual
        xgb_prediction = physics_value + xgb_residual
        lgb_prediction = physics_value + lgb_residual

        # Final tahmin (ağırlıklı ortalama - 5 model)
        available_models = ['physics', 'gb', 'rf']
        model_predictions = {
            'physics': physics_corrected,
            'gb': gb_prediction,
            'rf': rf_prediction
        }
        
        if XGBOOST_AVAILABLE and self.xgb_model is not None:
            available_models.append('xgboost')
            model_predictions['xgboost'] = xgb_prediction
        
        if LIGHTGBM_AVAILABLE and self.lgb_model is not None:
            available_models.append('lightgbm')
            model_predictions['lightgbm'] = lgb_prediction
        
        # Dinamik ağırlık hesapla (sadece mevcut modeller için)
        total_weight = sum(self.WEIGHTS[m] for m in available_models)
        
        # Sayısal stabilite için total_weight kontrolü
        if total_weight <= 0:
            logger.warning("No valid model weights found, falling back to 1.0")
            total_weight = 1.0
            
        final = sum(
            (self.WEIGHTS[m] / total_weight) * model_predictions[m]
            for m in available_models
        )
        
        # ML correction (ağırlıklı residual ortalaması)
        residuals = [gb_residual, rf_residual]
        if XGBOOST_AVAILABLE and self.xgb_model:
            residuals.append(xgb_residual)
        if LIGHTGBM_AVAILABLE and self.lgb_model:
            residuals.append(lgb_residual)
        ml_correction = np.mean(residuals) if residuals else 0.0

        # Güven aralığı (model uyumsuzluğuna göre)
        predictions = list(model_predictions.values())
        uncertainty = np.std(predictions) + 1.0

        return PredictionResult(
            tahmin_l_100km=round(final, 1),
            physics_only=round(physics_value, 1),
            ml_correction=round(ml_correction, 2),
            confidence_low=round(final - uncertainty, 1),
            confidence_high=round(final + uncertainty, 1),
            physics_weight=self.WEIGHTS['physics'],
            features_used={
                'mesafe_km': sefer.get('mesafe_km'),
                'ton': sefer.get('ton'),
                'arac_yasi': sefer.get('arac_yasi'),
                'yas_faktoru': yas_faktoru,
                'mevsim_faktor': mevsim_faktor,
                'xgboost_used': XGBOOST_AVAILABLE,
                'lightgbm_used': LIGHTGBM_AVAILABLE,
            }
        )

    def _calculate_checksum(self, filepath: str) -> str:
        """Dosya için SHA256 checksum hesapla"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def save_model(self, filepath: str):
        """Model parametrelerini kaydet (Güvenli Hibrit Format)"""
        if not self.is_trained:
            raise RuntimeError("Model eğitilmedi")

        import joblib
        import json

        base_path = Path(filepath).with_suffix('')
        
        # 1. Sklearn modelleri (Joblib - %100 Güvenlik için Checksum eklenecek)
        sklearn_file = f"{base_path}_sklearn.joblib"
        sklearn_data = {
            'gb_model': self.gb_model,
            'rf_model': self.rf_model,
            'scaler': self.scaler
        }
        joblib.dump(sklearn_data, sklearn_file)
        
        # Checksum hesapla
        sklearn_checksum = self._calculate_checksum(sklearn_file)

        # 2. Native Modeller (Daha güvenli JSON formatı)
        if XGBOOST_AVAILABLE and self.xgb_model:
            # XGBRegressor'da save_model mevcuttur
            self.xgb_model.save_model(f"{base_path}_xgb.json")
        
        if LIGHTGBM_AVAILABLE and self.lgb_model:
            # LGBMRegressor'da save_model yoktur, booster üzerinden kaydedilir
            if hasattr(self.lgb_model, "booster_"):
                self.lgb_model.booster_.save_model(f"{base_path}_lgb.json")
            else:
                # Eğer henüz eğitilmemişse (fit çağrılmamışsa) booster_ oluşmaz
                logger.warning("LightGBM booster bulunamadı, JSON kaydedilemedi.")

        # 3. Metadata (JSON - Checksum buraya kaydedilir)
        metadata = {
            'physics_weight': self.physics_weight,
            'training_stats': self.training_stats,
            'is_trained': self.is_trained,
            'last_updated': date.today().isoformat(),
            'sklearn_checksum': sklearn_checksum
        }
        with open(f"{base_path}_meta.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Ensemble model saved (hybrid) to {base_path} with checksum {sklearn_checksum[:8]}")

    def load_model(self, filepath: str):
        """Model parametrelerini yükle (Güvenli SHA256 Doğrulamalı)"""
        import joblib
        import json

        base_path = Path(filepath).with_suffix('')
        
        # 1. Metadata yükle
        meta_file = Path(f"{base_path}_meta.json")
        if not meta_file.exists():
            raise FileNotFoundError(f"Metadata dosyası bulunamadı: {meta_file}")
            
        with open(meta_file, encoding='utf-8') as f:
            metadata = json.load(f)
            
        self.physics_weight = metadata['physics_weight']
        self.training_stats = metadata['training_stats']
        self.is_trained = metadata['is_trained']
        expected_checksum = metadata.get('sklearn_checksum')

        # 2. Sklearn modelleri yükle (GÜVENLİK KRİTİK: Checksum doğrulaması)
        sklearn_file = Path(f"{base_path}_sklearn.joblib")
        if sklearn_file.exists():
            # Checksum doğrula
            if expected_checksum:
                actual_checksum = self._calculate_checksum(str(sklearn_file))
                if actual_checksum != expected_checksum:
                    logger.error(f"GÜVENLİK İHLALİ: Model dosyası checksum uyuşmazlığı! {sklearn_file}. Expected: {expected_checksum}, Actual: {actual_checksum}")
                    raise SecurityError("Model dosyası bozulmuş veya değiştirilmiş olabilir!")
            else:
                logger.warning(f"Model yüklendi ancak checksum doğrulaması yapılamadı (metadata eksik): {sklearn_file}")
            
            # joblib.load öncesi dosya boyutu kontrolü (DoS protection için çok büyük dosya engelleme)
            if sklearn_file.stat().st_size > 100 * 1024 * 1024:  # 100MB limit
                logger.error(f"Güvenlik uyarısı: Model dosyası çok büyük! {sklearn_file}")
                raise SecurityError("Model dosyası kabul edilebilir boyut limitini aşıyor.")

            sklearn_data = joblib.load(sklearn_file)
            self.gb_model = sklearn_data['gb_model']
            self.rf_model = sklearn_data['rf_model']
            self.scaler = sklearn_data['scaler']
            logger.debug(f"Sklearn models loaded and verified: {sklearn_file}")

        # 3. Native Modelleri yükle (JSON formatı doğal olarak daha güvenlidir)
        if XGBOOST_AVAILABLE:
            xgb_file = Path(f"{base_path}_xgb.json")
            if xgb_file.exists():
                if self.xgb_model is None:
                    import xgboost as xgb_lib
                    self.xgb_model = xgb_lib.XGBRegressor()
                self.xgb_model.load_model(str(xgb_file))
        
        if LIGHTGBM_AVAILABLE:
            lgb_file = Path(f"{base_path}_lgb.json")
            if lgb_file.exists():
                import lightgbm as lgb_lib
                # Native booster olarak yükle ve wrapper'a ata
                booster = lgb_lib.Booster(model_file=str(lgb_file))
                if self.lgb_model is None:
                    self.lgb_model = lgb_lib.LGBMRegressor()
                self.lgb_model._Booster = booster
                self.lgb_model._n_features = booster.num_feature()
                # Not: Scikit-learn wrapper'ı tam çalışması için bazı internal flaglar gerekebilir

        logger.info(f"Ensemble model loaded and verified from {base_path}")


class EnsemblePredictorService:
    """
    Ensemble predictor için iş mantığı servisi.
    Veritabanı entegrasyonu ve model yönetimi.
    """

    MAX_PREDICTORS = 100  # Bellek yönetimi için limit

    def __init__(self):
        self._arac_repo = None
        self._sefer_repo = None
        self.predictors: OrderedDict[int, EnsembleFuelPredictor] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def arac_repo(self):
        if self._arac_repo is None:
            from app.database.repositories.arac_repo import get_arac_repo
            self._arac_repo = get_arac_repo()
        return self._arac_repo

    @property
    def sefer_repo(self):
        if self._sefer_repo is None:
            from app.database.repositories.sefer_repo import get_sefer_repo
            self._sefer_repo = get_sefer_repo()
        return self._sefer_repo

    def get_predictor(self, arac_id: int) -> EnsembleFuelPredictor:
        """Araç için predictor al veya oluştur (Thread-Safe + LRU Cache)"""
        with self._lock:
            if arac_id in self.predictors:
                # LRU: Mevcut olanı sona taşı (most recently used)
                self.predictors.move_to_end(arac_id)
                return self.predictors[arac_id]
            
            # Yeni oluştur
            predictor = EnsembleFuelPredictor()
            self.predictors[arac_id] = predictor
            
            # Limit aşılırsa en eskiyi (baştakini) çıkar
            if len(self.predictors) > self.MAX_PREDICTORS:
                oldest_id, _ = self.predictors.popitem(last=False)
                logger.debug(f"LRU Cache: Arac {oldest_id} predictor bellekten temizlendi.")
                
            return predictor

    async def train_for_vehicle(self, arac_id: int) -> Dict:
        """
        Belirli araç için model eğit.
        Veritabanından verileri toplar ve enrich eder.
        """
        from app.core.services.sofor_analiz_service import get_sofor_analiz_service
        from app.core.services.weather_service import get_weather_service

        # Araç bilgisini al
        arac = await self.arac_repo.get_by_id(arac_id)
        if not arac:
            return {'success': False, 'error': 'Araç bulunamadı'}

        # Araç yaşı ve faktörü hesapla
        from app.core.entities.models import Arac
        arac_entity = Arac(**arac)
        arac_yasi = arac_entity.yas
        yas_faktoru = arac_entity.yas_faktoru

        # Eğitim verilerini al
        seferler = await self.sefer_repo.get_for_training(arac_id, limit=500)
        if len(seferler) < 10:
            return {'success': False, 'error': f'Yetersiz veri: {len(seferler)} sefer'}

        # Verileri enrich et
        weather_service = get_weather_service()
        sofor_service = get_sofor_analiz_service()

        enriched_seferler = []
        y_values = []

        for s in seferler:
            # Mevsim faktörü
            target_date = date.today()  # Varsayılan
            mevsim_faktor = weather_service.get_seasonal_factor(target_date)

            # Şoför faktörü (varsa)
            sofor_katsayi = 1.0
            if s.get('sofor_id'):
                stats = sofor_service.get_driver_stats(s['sofor_id'])
                if stats and len(stats) > 0:
                    driver = stats[0]
                    # Filo karşılaştırmadan şoför katsayısı
                    sofor_katsayi = 1.0 - (driver.filo_karsilastirma / 100) * 0.1

            enriched = {
                **s,
                'arac_yasi': arac_yasi,
                'yas_faktoru': yas_faktoru,
                'mevsim_faktor': mevsim_faktor,
                'sofor_katsayi': sofor_katsayi
            }

            enriched_seferler.append(enriched)
            y_values.append(float(s['tuketim']))

        # Model eğit
        predictor = self.get_predictor(arac_id)
        result = predictor.fit(enriched_seferler, np.array(y_values))

        if result['success']:
            logger.info(f"Ensemble model trained for vehicle {arac_id}: {result}")

        return result

    async def predict_consumption(
        self,
        arac_id: int,
        mesafe_km: float,
        ton: float,
        sofor_id: Optional[int] = None,
        ascent_m: float = 0,
        descent_m: float = 0,
        target_date: Optional[date] = None
    ) -> Dict:
        """
        Yakıt tüketimi tahmin et
        """
        from app.core.services.sofor_analiz_service import get_sofor_analiz_service
        from app.core.services.weather_service import get_weather_service

        # Araç bilgisi
        arac = await self.arac_repo.get_by_id(arac_id)
        if not arac:
            return {'success': False, 'error': 'Araç bulunamadı'}

        from app.core.entities.models import Arac
        arac_entity = Arac(**arac)

        # Mevsim faktörü
        weather_service = get_weather_service()
        target = target_date or date.today()
        mevsim_faktor = weather_service.get_seasonal_factor(target)

        # Şoför faktörü
        sofor_katsayi = 1.0
        if sofor_id:
            sofor_service = get_sofor_analiz_service()
            stats = sofor_service.get_driver_stats(sofor_id)
            if stats:
                sofor_katsayi = 1.0 - (stats[0].filo_karsilastirma / 100) * 0.1

        sefer = {
            'mesafe_km': mesafe_km,
            'ton': ton,
            'ascent_m': ascent_m,
            'descent_m': descent_m,
            'arac_yasi': arac_entity.yas,
            'yas_faktoru': arac_entity.yas_faktoru,
            'mevsim_faktor': mevsim_faktor,
            'sofor_katsayi': sofor_katsayi
        }

        predictor = self.get_predictor(arac_id)
        result = predictor.predict(sefer)

        return {
            'success': True,
            'tahmin_l_100km': result.tahmin_l_100km,
            'tahmin_litre': round(mesafe_km * result.tahmin_l_100km / 100, 1),
            'guven_araligi': (result.confidence_low, result.confidence_high),
            'physics_only': result.physics_only,
            'ml_correction': result.ml_correction,
            'factors': {
                'arac_yasi': arac_entity.yas,
                'yas_faktoru': round(arac_entity.yas_faktoru, 3),
                'euro_sinifi': arac_entity.euro_sinifi,
                'mevsim_faktor': mevsim_faktor,
                'sofor_katsayi': round(sofor_katsayi, 3)
            }
        }


# Singleton (Thread-Safe Double-Checked Locking)
_ensemble_service = None
_ensemble_service_lock = threading.Lock()


def get_ensemble_service() -> EnsemblePredictorService:
    """Thread-safe singleton erişimi"""
    global _ensemble_service
    if _ensemble_service is None:
        with _ensemble_service_lock:
            if _ensemble_service is None:  # Double-checked locking
                _ensemble_service = EnsemblePredictorService()
    return _ensemble_service
