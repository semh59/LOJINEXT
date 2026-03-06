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
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    RouteConditions,
    VehicleSpecs,
)
from app.core.ml.ensemble_strategy import EnsembleStrategy, DynamicWeightStrategy
from app.infrastructure.logging.logger import get_logger


class SecurityError(Exception):
    """Güvenlik ihlali durumunda fırlatılan istisna"""

    pass


# Sklearn importları (lazy loading ile)
try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.metrics import r2_score
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
    Hibrit Ensemble Model (5 Model Kombinasyonu):
    1. Fizik bazlı base tahmin (%10)
    2. LightGBM - Kategorik feature handling (%15)
    3. XGBoost - Dominant gradient boosting (%55)
    4. GradientBoosting - Sklearn baseline (%10)
    5. RandomForest - Variance reduction (%10)

    Feature'lar (24 adet):
    Phase 2G (16): ton, ascent_m, descent_m, net_elevation,
      yuk_yogunlugu, zorluk, arac_yasi, yas_faktoru,
      mevsim_faktor, sofor_katsayisi,
      motorway_ratio, trunk_ratio, primary_ratio,
      residential_ratio, unclassified_ratio, flat_km
    Phase 5A TIR Physics (8): grade_gentle_ratio, grade_moderate_ratio,
      grade_steep_ratio, weight_x_gradient, stopgo_proxy,
      aero_speed_factor, engine_load_proxy, route_fatigue
    """

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
        # Route Analysis Features (Phase 2G)
        "motorway_ratio",
        "trunk_ratio",
        "primary_ratio",
        "residential_ratio",
        "unclassified_ratio",
        "flat_km",
        # TIR Physics Features (Phase 5A - Refined)
        "grade_gentle_ratio",  # 0–2.5%
        "grade_moderate_ratio",  # 2.5–5.5%
        "grade_steep_ratio",  # 5.5%+
        "weight_x_gradient",  # ton × (ascent / (mesafe + 1))
        "stopgo_proxy",  # residential_ratio × sqrt(mesafe)
        "aero_speed_factor",  # motorway_ratio × Cd proxy
        "engine_load_proxy",  # (1 - flat_ratio)^1.3 × load_ratio
        "route_fatigue",  # proxy via duration
        "dorse_bos_agirlik",
        "dorse_lastik_sayisi",
    ]

    # Varsayılan ağırlıklar (Dürüstlük Protokolü: Fizik Dominant)
    DEFAULT_WEIGHTS = {
        "physics": 0.80,  # Cold Start: Fizik modeline güveniyoruz
        "lightgbm": 0.05,
        "xgboost": 0.05,
        "gb": 0.05,
        "rf": 0.05,
    }

    def __init__(
        self, vehicle_specs: VehicleSpecs = None, strategy: EnsembleStrategy = None
    ):
        import hashlib

        self._feature_hash = hashlib.sha256(
            "".join(self.FEATURE_NAMES).encode()
        ).hexdigest()[:16]
        self._physics_version = "v5.2-hybrid"
        self.physics_model = PhysicsBasedFuelPredictor(vehicle_specs)
        self.weights = self.DEFAULT_WEIGHTS.copy()  # Instance-specific weights
        self.strategy = strategy if strategy is not None else DynamicWeightStrategy()

        # GradientBoosting
        if SKLEARN_AVAILABLE:
            self.gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )

            self.rf_model = RandomForestRegressor(
                n_estimators=50, max_depth=6, random_state=42
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
                n_estimators=50,  # Reduced from 200
                max_depth=2,  # Shallow depth to prevent overfitting
                learning_rate=0.05,  # Slower learning
                min_child_weight=2,  # Regularization
                subsample=0.7,
                colsample_bytree=0.7,
                objective="reg:squarederror",
                random_state=42,
                verbosity=0,
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
                random_state=42,
            )
            logger.info("LightGBM model initialized")
        else:
            self.lgb_model = None
            logger.warning("LightGBM not available, excluding from ensemble")

        self.is_trained = False
        self.physics_weight = self.weights.get("physics", 0.2)
        self.training_stats = {}
        self._model_lock = (
            threading.Lock()
        )  # Tahmin ve eğitim arasında senkronizasyon için

    def prepare_features(self, seferler: List[Dict]) -> np.ndarray:
        """
        Feature engineering — Tüm faktörleri çıkar.
        Phase 2G: Route analysis features (16)
        Phase 5A: TIR physics features (8) — Total: 24
        """
        import math

        features = []

        zorluk_map = {"Kolay": 1, "Normal": 2, "Zor": 3, "Çok Zor": 4}

        for s in seferler:
            # ── Base Features ──
            mesafe = float(s.get("mesafe_km", 0) or 0)
            ton = float(s.get("ton", 0) or 0)
            ascent = float(s.get("ascent_m", 0) or 0)
            descent = float(s.get("descent_m", 0) or 0)
            flat_km = float(s.get("flat_distance_km", 0) or 0)

            # Derived
            net_elevation = ascent - descent
            yuk_yogunlugu = ton / mesafe if mesafe > 0 else 0
            zorluk = zorluk_map.get(s.get("zorluk", "Normal"), 2)

            # Vehicle age
            arac_yasi = float(s.get("arac_yasi", 5) or 5)
            yas_faktoru = float(s.get("yas_faktoru", 1.0) or 1.0)

            # Season & driver
            mevsim_faktor = float(s.get("mevsim_faktor", 1.0) or 1.0)
            sofor_katsayi = float(s.get("sofor_katsayi", 1.0) or 1.0)

            # Dorse Features (Phase 4)
            dorse_bos_agirlik = float(s.get("dorse_bos_agirlik", 6500.0) or 6500.0)
            dorse_lastik_sayisi = float(s.get("dorse_lastik_sayisi", 6) or 6)

            # ── Route Analysis (Phase 2G) ──
            motorway_ratio = 0.0
            trunk_ratio = 0.0
            primary_ratio = 0.0
            residential_ratio = 0.0
            unclassified_ratio = 0.0

            rota_detay = s.get("rota_detay") or {}
            # Support both nested and flat format
            analysis = rota_detay.get("route_analysis") or rota_detay

            # Grade distribution defaults (Phase 5A)
            grade_gentle_ratio = 1.0  # Default: assume all gentle if no data
            grade_moderate_ratio = 0.0
            grade_steep_ratio = 0.0

            if analysis and mesafe > 0:

                def sum_km(cat_dict):
                    """Sum flat+up+down for a road category."""
                    if not cat_dict or not isinstance(cat_dict, dict):
                        return 0.0
                    return (
                        float(cat_dict.get("flat", 0))
                        + float(cat_dict.get("up", 0))
                        + float(cat_dict.get("down", 0))
                    )

                motorway_km = sum_km(analysis.get("motorway"))
                trunk_km = sum_km(analysis.get("trunk"))
                primary_km = sum_km(analysis.get("primary"))
                residential_km = sum_km(analysis.get("residential"))
                unclassified_km = sum_km(analysis.get("unclassified"))

                motorway_ratio = min(1.0, motorway_km / mesafe)
                trunk_ratio = min(1.0, trunk_km / mesafe)
                primary_ratio = min(1.0, primary_km / mesafe)
                residential_ratio = min(1.0, residential_km / mesafe)
                unclassified_ratio = min(1.0, unclassified_km / mesafe)

                # ── Grade Histogram (Phase 5A Refined) ──
                # gentle (0-2.5%), moderate (2.5-5.5%), steep (5.5%+)
                total_up_down = 0.0
                gentle_km = 0.0
                moderate_km = 0.0
                steep_km = 0.0

                for cat_name in [
                    "motorway",
                    "trunk",
                    "primary",
                    "residential",
                    "unclassified",
                    "other",
                ]:
                    cat = analysis.get(cat_name)
                    if not cat or not isinstance(cat, dict):
                        continue
                    up_km = float(cat.get("up", 0))
                    down_km = float(cat.get("down", 0))
                    cat_updown = up_km + down_km
                    total_up_down += cat_updown

                    if cat_name in ("motorway", "trunk"):
                        gentle_km += cat_updown
                    elif cat_name == "primary":
                        # Primary roads: ~70% moderate, ~30% gentle
                        moderate_km += cat_updown * 0.7
                        gentle_km += cat_updown * 0.3
                    else:
                        # Residential/Rural: ~50% steep, ~30% moderate, ~20% gentle
                        steep_km += cat_updown * 0.5
                        moderate_km += cat_updown * 0.3
                        gentle_km += cat_updown * 0.2

                total_graded = flat_km + total_up_down
                if total_graded > 0:
                    grade_gentle_ratio = min(1.0, (flat_km + gentle_km) / total_graded)
                    grade_moderate_ratio = min(1.0, moderate_km / total_graded)
                    grade_steep_ratio = min(1.0, steep_km / total_graded)

            # ── Elite TIR Interaction Refinements (Phase 5A) ──

            # 1. Weight × Gradient: "ağır yük + rampa" (Stabilized)
            weight_x_gradient = ton * (ascent / (mesafe + 1.0))

            # 2. Stop-go proxy: Non-linear (Power law)
            # residential_ratio × sqrt(mesafe) — captures acceleration cycle intensity
            stopgo_proxy = residential_ratio * math.sqrt(mesafe)

            # 3. Aerodynamic speed factor: Cd proxy
            aero_speed_factor = motorway_ratio * (1.0 + trunk_ratio * 0.3)

            # 4. Engine load proxy: Exponential stress
            # (1 - flat_ratio)^1.3 × load_ratio
            non_flat_ratio = 1.0 - (flat_km / mesafe) if mesafe > 0 else 0
            load_ratio = ton / 26.0
            engine_load_proxy = (non_flat_ratio**1.3) * load_ratio

            # 5. Route Fatigue: duration proxy (Phase 5A Extra)
            duration_min = float(s.get("duration_min") or (mesafe / 70 * 60) or 0)
            route_fatigue = min(
                1.0, duration_min / 600.0
            )  # fatigue caps at 600 mins (10h)

            features.append(
                [
                    ton,
                    ascent,
                    descent,
                    net_elevation,
                    yuk_yogunlugu,
                    zorluk,
                    arac_yasi,
                    yas_faktoru,
                    mevsim_faktor,
                    sofor_katsayi,
                    motorway_ratio,
                    trunk_ratio,
                    primary_ratio,
                    residential_ratio,
                    unclassified_ratio,
                    flat_km,
                    grade_gentle_ratio,
                    grade_moderate_ratio,
                    grade_steep_ratio,
                    weight_x_gradient,
                    stopgo_proxy,
                    aero_speed_factor,
                    engine_load_proxy,
                    route_fatigue,
                    dorse_bos_agirlik,
                    dorse_lastik_sayisi,
                ]
            )

        return np.array(features)

    def _get_physics_predictions(self, seferler: List[Dict]) -> np.ndarray:
        """Fizik modeli tahminleri"""
        predictions = []

        for s in seferler:
            route = RouteConditions(
                distance_km=float(s.get("mesafe_km", 0) or 0),
                load_ton=float(s.get("ton", 0) or 0),
                is_empty_trip=bool(s.get("is_empty_trip", False)),
                ascent_m=float(s.get("ascent_m", 0) or 0),
                descent_m=float(s.get("descent_m", 0) or 0),
            )
            # Apply dynamic specs to model if available in sefer dict
            if "dorse_bos_agirlik" in s:
                self.physics_model.vehicle.trailer_empty_weight_kg = s[
                    "dorse_bos_agirlik"
                ]
            if "dorse_lastik_direnci" in s:
                self.physics_model.vehicle.trailer_rolling_resistance = s[
                    "dorse_lastik_direnci"
                ]
            if "dorse_hava_direnci" in s:
                self.physics_model.vehicle.trailer_drag_contribution = s[
                    "dorse_hava_direnci"
                ]

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
                "success": False,
                "error": f"Yetersiz veri: {len(seferler)} sefer. En az 10 gerekli.",
            }

        if not SKLEARN_AVAILABLE:
            return {"success": False, "error": "sklearn kütüphanesi yüklü değil."}

        try:
            # LOCK SCOPE FIX: Tüm eğitim lock içinde - is_trained flag atomik güncellemesi
            with self._model_lock:
                self.is_trained = False  # Eğitim sırasında eski tahminleri engelle

                # ML Outlier Guard (Z-score > 3.0)
                if len(y_actual) > 20:
                    y_mean = np.mean(y_actual)
                    y_std = np.std(y_actual)
                    if y_std > 0:
                        z_scores = np.abs((y_actual - y_mean) / y_std)
                        mask = z_scores < 3.0
                        removed = int(len(y_actual) - np.sum(mask))
                        if removed > 0:
                            logger.info(
                                f"ML Outlier Guard: {removed} samples removed from training."
                            )
                            y_actual = y_actual[mask]
                            seferler = [s for i, s in enumerate(seferler) if mask[i]]

                # Temporal Weighting — eski veri düşük ağırlık, yeni veri yüksek
                from datetime import date as dt_date

                bugun = dt_date.today()
                sample_weights = []
                for s in seferler:
                    tarih_str = s.get("tarih")
                    if tarih_str:
                        try:
                            if isinstance(tarih_str, str):
                                tarih = dt_date.fromisoformat(tarih_str)
                            elif isinstance(tarih_str, dt_date):
                                tarih = tarih_str
                            else:
                                tarih = bugun
                            ay_farki = max(0, (bugun - tarih).days / 30.0)
                            # Alpha: 0.1 (Phase 7 Request - Give 2025 much more weight than 2022)
                            weight = np.exp(-0.1 * ay_farki)
                        except (ValueError, TypeError):
                            weight = 0.5
                    else:
                        weight = 0.5

                    # NaN Guard for weight
                    if not np.isfinite(weight):
                        weight = 0.1

                    sample_weights.append(max(0.1, weight))  # Minimum %10 ağırlık
                sample_weights = np.array(sample_weights)
                logger.info(
                    f"Temporal Weighting: min={sample_weights.min():.2f}, "
                    f"max={sample_weights.max():.2f}, mean={sample_weights.mean():.2f}"
                )

                # Feature hazırla
                X = self.prepare_features(seferler)
                X_scaled = self.scaler.fit_transform(X)

                # Fizik tahminleri (Baseline L/100km)
                y_physics_raw = self._get_physics_predictions(seferler)

                # Phase 5A Elite Fix: Apply yas_faktoru and mevsim_faktor to BASELINE
                # This prevents ML from learning these factors twice (Double Factor Trap)
                y_physics_factored = []
                for i, s in enumerate(seferler):
                    yas_f = float(s.get("yas_faktoru", 1.0) or 1.0)
                    mevsim_f = float(s.get("mevsim_faktor", 1.0) or 1.0)
                    y_physics_factored.append(y_physics_raw[i] * yas_f * mevsim_f)
                y_physics = np.array(y_physics_factored)

                # Database'den gelen 'tuketim' zaten L/100km formatında (Kritik Keşif)
                # Elite Fix: 'tuketim' doğrudan kullanılıyor (Double Division bug engellendi)
                y_norm = []
                for i, s in enumerate(seferler):
                    val = float(y_actual[i] or 0.0)
                    if val > 0:
                        y_norm.append(val)
                    else:
                        y_norm.append(y_physics[i])  # Fallback
                y_norm = np.array(y_norm)

                # Residual = Gerçek (L/100km) - Factored Physics (L/100km)
                residuals = y_norm - y_physics

                # Debug Logging for Elite Analysis
                if len(residuals) > 0:
                    logger.info(
                        f"ML FIT DEBUG [Vehicle]: y_norm mean={np.mean(y_norm):.2f}, y_phys mean={np.mean(y_physics):.2f}, resid mean={np.mean(residuals):.2f}"
                    )
                    logger.info(
                        f"ML FIT DEBUG [Vehicle]: y_norm range=[{np.min(y_norm):.2f}, {np.max(y_norm):.2f}], residuals std={np.std(residuals):.2f}"
                    )

                # Phase 3 Elite: Train/Test Split (Overfitting Guard)
                # 15+ örnek varsa dürüstlük için ayır, yoksa CV ile devam et
                use_split = len(residuals) >= 15
                if use_split:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X_scaled, residuals, test_size=0.2, random_state=42
                    )
                else:
                    X_train, y_train = X_scaled, residuals
                    X_test, y_test = X_scaled, residuals

                # ML modelleri eğit (Training set üzerinde - Temporal Weighted)
                # sample_weight split'e göre ayarla
                if use_split:
                    # train_test_split indekslerini kullanarak ağırlıkları da bölelim
                    sw_train = (
                        sample_weights[: len(X_train)]
                        if len(sample_weights) >= len(X_train)
                        else None
                    )
                else:
                    sw_train = (
                        sample_weights if len(sample_weights) == len(X_train) else None
                    )

                self.gb_model.fit(X_train, y_train, sample_weight=sw_train)
                self.rf_model.fit(X_train, y_train, sample_weight=sw_train)

                # Feature Importance (Explainability)
                # FEATURE_NAMES ile senkron (17 isim) — BUG-1 FIX
                importances = self.rf_model.feature_importances_
                feat_imp = {
                    name: round(float(imp), 4)
                    for name, imp in zip(self.FEATURE_NAMES, importances)
                }

                # XGBoost eğitimi
                xgb_r2 = 0.0
                if self.xgb_model is not None:
                    self.xgb_model.fit(X_train, y_train, sample_weight=sw_train)
                    xgb_test_pred = self.xgb_model.predict(X_test)
                    xgb_r2 = r2_score(y_test, xgb_test_pred) if len(y_test) > 0 else 0

                # LightGBM eğitimi
                lgb_r2 = 0.0
                if LIGHTGBM_AVAILABLE and self.lgb_model is not None:
                    self.lgb_model.fit(X_train, y_train, sample_weight=sw_train)
                    lgb_test_pred = self.lgb_model.predict(X_test)
                    lgb_r2 = r2_score(y_test, lgb_test_pred) if len(y_test) > 0 else 0

                # Dürüst Test Skorları (GB & RF)
                gb_test_r2 = (
                    r2_score(y_test, self.gb_model.predict(X_test))
                    if len(y_test) > 0
                    else 0
                )
                rf_test_r2 = (
                    r2_score(y_test, self.rf_model.predict(X_test))
                    if len(y_test) > 0
                    else 0
                )

                # Cross-validation skorları (Training set üzerinde dürüstlük için)
                cv_folds = min(5, max(2, len(X_train) // 2))
                gb_cv_mean = 0.0
                if cv_folds >= 2:
                    gb_cv_scores = cross_val_score(
                        self.gb_model, X_train, y_train, cv=cv_folds, scoring="r2"
                    )
                    gb_cv_mean = np.mean(gb_cv_scores)

                # ---------------------------------------------------------
                # STRATEGY BASED WEIGHTING (Faz 2)
                # ---------------------------------------------------------
                # 1. Pozitif R2 skoru olan modelleri belirle
                metrics_for_strategy = {
                    "gb": {"r2": max(0, gb_test_r2)},
                    "rf": {"r2": max(0, rf_test_r2)},
                    "xgboost": {"r2": max(0, xgb_r2) if xgb_r2 else 0},
                    "lightgbm": {"r2": max(0, lgb_r2) if lgb_r2 else 0},
                }
                avail_models = ["gb", "rf", "xgboost", "lightgbm"]

                ml_weights = self.strategy.calculate_weights(
                    metrics_for_strategy, avail_models
                )

                base_physics_weight = 0.10
                ml_total_r2 = sum(m["r2"] for m in metrics_for_strategy.values())

                new_weights = {}
                if ml_total_r2 > 0:
                    # ML modelleri başarılı, kalan payı stratejinin döndüğü oranlarla dağıt
                    ml_share = 1.0 - base_physics_weight
                    new_weights["physics"] = base_physics_weight

                    for model in avail_models:
                        weight = ml_weights.get(model, 0.0) * ml_share
                        new_weights[model] = round(weight, 3)
                else:
                    # Hiçbir ML modeli başarılı değil -> Fallback to Physics
                    logger.warning(
                        "Dynamic Weighting: All ML models failed (R2<=0). Fallback to Physics."
                    )
                    new_weights = {
                        "physics": 1.0,
                        "gb": 0,
                        "rf": 0,
                        "xgboost": 0,
                        "lightgbm": 0,
                    }

                # Ağırlıkları normalize et (toplam = 1.0)
                total_w = sum(new_weights.values())
                if total_w > 0:
                    self.weights = {k: v / total_w for k, v in new_weights.items()}
                else:
                    self.weights = self.DEFAULT_WEIGHTS.copy()

                self.physics_weight = self.weights.get("physics", 1.0)

                # ---------------------------------------------------------
                # EXTENDED METRICS (Faz 2)
                # ---------------------------------------------------------
                # Test seti üzerinde Ensemble performansını ölç
                final_preds = []
                for i in range(len(X_test)):
                    # Get factored physics baseline for this test sample
                    p_physics = (
                        y_physics[len(y_train) + i] if use_split else y_physics[i]
                    )

                    weighted_res = 0.0
                    # GB
                    if self.weights.get("gb", 0) > 0:
                        weighted_res += (
                            self.weights["gb"] * self.gb_model.predict([X_test[i]])[0]
                        )
                    # RF
                    if self.weights.get("rf", 0) > 0:
                        weighted_res += (
                            self.weights["rf"] * self.rf_model.predict([X_test[i]])[0]
                        )
                    # XGB
                    if self.weights.get("xgboost", 0) > 0 and self.xgb_model:
                        weighted_res += (
                            self.weights["xgboost"]
                            * self.xgb_model.predict([X_test[i]])[0]
                        )
                    # LGBM
                    if self.weights.get("lightgbm", 0) > 0 and self.lgb_model:
                        weighted_res += (
                            self.weights["lightgbm"]
                            * self.lgb_model.predict([X_test[i]])[0]
                        )

                    final_preds.append(p_physics + weighted_res)

                final_preds = np.array(final_preds)

                # Metrik hesapla (Test seti: y_test = actual_residuals)
                # y_test = y_actual - y_physics
                # Bizim final_pred - p_physics = weighted_residual_sum
                # Hata = (p_physics + weighted_residual_sum) - (p_physics + y_test)
                #      = weighted_residual_sum - y_test

                y_true = y_physics[-len(y_test) :] + y_test
                errors = final_preds - y_true
                mae = np.mean(np.abs(errors))
                rmse = np.sqrt(np.mean(errors**2))

                # Ensemble R2 Score calculation
                ens_r2 = 0.0
                if SKLEARN_AVAILABLE:
                    try:
                        from sklearn.metrics import r2_score as r2_metrics_func

                        ens_r2 = r2_metrics_func(y_true, final_preds)
                    except Exception as e:
                        logger.warning(f"Could not calculate ensemble R2: {e}")

                mape = np.mean(np.abs(errors / np.maximum(np.abs(y_true), 1e-6))) * 100

                physics_mae = np.mean(np.abs(y_test))

                self.training_stats = {
                    "sample_count": len(seferler),
                    "test_size": len(y_test) if use_split else 0,
                    "ensemble_r2": round(float(ens_r2), 4),
                    "measurements": {
                        "mae": round(mae, 2),
                        "rmse": round(rmse, 2),
                        "mape": round(mape, 2),
                        "physics_mae": round(physics_mae, 2),
                    },
                    "metrics": {
                        "gb_test_r2": round(gb_test_r2, 3),
                        "rf_test_r2": round(rf_test_r2, 3),
                        "xgb_test_r2": round(float(xgb_r2), 3) if xgb_r2 else None,
                        "lgb_test_r2": round(float(lgb_r2), 3) if lgb_r2 else None,
                        "gb_cv_mean": round(float(gb_cv_mean), 3),
                    },
                    "feature_importance": feat_imp,
                    "model_weights": self.weights,
                    "is_honest_test": use_split,
                }

                # is_trained bayrağı lock içinde - RACE CONDITION FIX
                self.is_trained = True

            return {"success": True, **self.training_stats}

        except Exception as e:
            logger.error(f"Ensemble training error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def predict(self, sefer: Dict) -> PredictionResult:
        """
        Tek sefer için tahmin.

        INPUT VALIDATION: Eksik veya hatalı veri kontrolü.
        """
        # INPUT VALIDATION: Zorunlu alan kontrolü
        mesafe = sefer.get("mesafe_km")
        if mesafe is None or (isinstance(mesafe, (int, float)) and mesafe <= 0):
            logger.warning(
                f"Geçersiz mesafe değeri: {mesafe}, varsayılan 100 kullanılıyor"
            )
            sefer = {**sefer, "mesafe_km": 100}

        # Physics prediction (always works)
        route = RouteConditions(
            distance_km=float(sefer.get("mesafe_km", 0) or 0),
            load_ton=float(sefer.get("ton", 0) or 0),
            is_empty_trip=bool(sefer.get("is_empty_trip", False)),  # Faz 3
            ascent_m=float(sefer.get("ascent_m", 0) or 0),
            descent_m=float(sefer.get("descent_m", 0) or 0),
            flat_distance_km=float(sefer.get("flat_distance_km", 0) or 0),
        )

        # Apply dynamic trailer specs to model if available in sefer dict
        if "dorse_bos_agirlik" in sefer:
            self.physics_model.vehicle.trailer_empty_weight_kg = float(
                sefer["dorse_bos_agirlik"] or 6500.0
            )
        if "dorse_lastik_direnci" in sefer:
            self.physics_model.vehicle.trailer_rolling_resistance = float(
                sefer["dorse_lastik_direnci"] or 0.006
            )
        if "dorse_hava_direnci" in sefer:
            self.physics_model.vehicle.trailer_drag_contribution = float(
                sefer["dorse_hava_direnci"] or 0.13
            )

        physics_pred = self.physics_model.predict(route)
        physics_raw = physics_pred.consumption_l_100km

        # Araç yaşı ve mevsim faktörünü uygula (Baseline)
        yas_faktoru = float(sefer.get("yas_faktoru", 1.0) or 1.0)
        mevsim_faktor = float(sefer.get("mevsim_faktor", 1.0) or 1.0)
        physics_value = physics_raw * yas_faktoru * mevsim_faktor

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
                    features_used=sefer,
                )

        # ML düzeltme (Residuals)
        X = self.prepare_features([sefer])
        X_scaled = self.scaler.transform(X)

        gb_residual = self.gb_model.predict(X_scaled)[0]
        rf_residual = self.rf_model.predict(X_scaled)[0]
        xgb_residual = self.xgb_model.predict(X_scaled)[0] if self.xgb_model else 0.0
        lgb_residual = (
            self.lgb_model.predict(X_scaled)[0]
            if (LIGHTGBM_AVAILABLE and self.lgb_model)
            else 0.0
        )

        # Model Bazlı Tahminler (Baseline + Residual)
        model_predictions = {
            "physics": physics_value,
            "gb": physics_value + gb_residual,
            "rf": physics_value + rf_residual,
        }

        if self.xgb_model:
            model_predictions["xgboost"] = physics_value + xgb_residual
        if self.lgb_model:
            model_predictions["lightgbm"] = physics_value + lgb_residual

        # Dinamik ağırlık hesapla
        active_model_keys = list(model_predictions.keys())
        total_weight = sum(self.weights.get(m, 0) for m in active_model_keys)

        # Guard against zero weights
        safe_total_w = total_weight if total_weight > 0 else 1.0

        final = sum(
            (self.weights.get(m, 0) / safe_total_w) * model_predictions[m]
            for m in active_model_keys
        )

        ml_correction = final - physics_value

        # NaN/Inf Guard — sessiz hatalı tahmin önleme
        if np.isnan(final) or np.isinf(final):
            logger.warning(
                f"NaN/Inf tahmin tespit edildi, physics-only fallback uygulanıyor | "
                f"final={final}, physics={physics_value}, "
                f"gb_res={gb_residual}, rf_res={rf_residual}, "
                f"xgb_res={xgb_residual}, lgb_res={lgb_residual}"
            )
            return PredictionResult(
                tahmin_l_100km=round(physics_value, 1),
                physics_only=round(physics_value, 1),
                ml_correction=0.0,
                confidence_low=round(physics_value * 0.85, 1),
                confidence_high=round(physics_value * 1.15, 1),
                physics_weight=1.0,
                features_used=sefer,
            )

        # Güven aralığı (Model uyuşmazlığı + Base uncertainty)
        all_preds = np.array(list(model_predictions.values()))
        # Ad-hoc but realistic: Std of models + 5% of prediction as floor
        uncertainty = np.std(all_preds) + (final * 0.05)

        return PredictionResult(
            tahmin_l_100km=round(final, 1),
            physics_only=round(physics_value, 1),
            ml_correction=round(ml_correction, 2),
            confidence_low=round(final - uncertainty, 1),
            confidence_high=round(final + uncertainty, 1),
            physics_weight=self.weights.get("physics", 0.2),
            features_used={
                **sefer,
                "yas_faktoru": yas_faktoru,
                "mevsim_faktor": mevsim_faktor,
            },
        )

    def explain_prediction(self, sefer: Dict) -> Dict:
        """
        Tahmin sonucunu açıkla (XAI - Explainable AI).
        Hassasiyet analizi (Sensitivity Analysis) kullanarak her feature'ın
        tahmin üzerindeki etkisini (L/100km delta) hesaplar.
        """
        # 1. Base tahmini al
        baseline_res = self.predict(sefer)
        base_val = baseline_res.tahmin_l_100km

        explanations = {}

        # 2. Önemli feature grupları üzerinde perturbasyon yap
        # Her feature'ı %10 artırıp/azaltıp tahmindeki değişime bakıyoruz (Simple Sensitivity)
        perturbation_targets = {
            "ton": "Yük",
            "ascent_m": "Yol Eğimi (Çıkış)",
            "zorluk": "Yol Zorluğu",
            "arac_yasi": "Araç Yaşı",
            "mevsim_faktor": "Mevsim Koşulları",
            "sofor_katsayi": "Sürücü Performansı",
            "motorway_ratio": "Otoyol Kullanımı",
            "stopgo_proxy": "Dur-Kalk Yoğunluğu",
        }

        for feature_key, display_name in perturbation_targets.items():
            if (
                feature_key not in sefer
                and feature_key not in baseline_res.features_used
            ):
                continue

            raw_val = baseline_res.features_used.get(feature_key, 0)

            # Değeri azaltmış gibi yapalım (etkiyi görmek için)
            test_sefer = sefer.copy()

            if feature_key == "zorluk":
                # Kategorik zorluk: Zor -> Normal, Normal -> Kolay
                current_zorluk = str(raw_val)
                z_map_inv = {
                    "Zor": "Normal",
                    "Çok Zor": "Zor",
                    "Normal": "Kolay",
                    "Kolay": "Kolay",
                }
                test_sefer[feature_key] = z_map_inv.get(current_zorluk, "Normal")
            else:
                # Sayısal değerler için %20 azaltma
                try:
                    val = float(raw_val)
                    test_sefer[feature_key] = val * 0.8
                except (ValueError, TypeError):
                    continue

            test_res = self.predict(test_sefer)
            delta = base_val - test_res.tahmin_l_100km

            # Etkiyi normalize et (Sadece anlamlı değişimleri raporla)
            if abs(delta) > 0.05:
                explanations[display_name] = round(delta, 2)

        # 3. Fizik motoru vs ML düzeltmesi bilgisini ekle
        explanations["ML Düzeltmesi"] = baseline_res.ml_correction

        return {
            "prediction": base_val,
            "unit": "L/100km",
            "contributions": explanations,
            "confidence": baseline_res.confidence_high - baseline_res.confidence_low,
        }

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

        import json

        import joblib

        base_path = Path(filepath).with_suffix("")

        # 1. Sklearn modelleri (Joblib - %100 Güvenlik için Checksum eklenecek)
        sklearn_file = f"{base_path}_sklearn.joblib"
        sklearn_data = {
            "gb_model": self.gb_model,
            "rf_model": self.rf_model,
            "xgb_model": self.xgb_model,
            "lgb_model": self.lgb_model,
            "scaler": self.scaler,
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
            "physics_weight": self.physics_weight,
            "training_stats": self.training_stats,
            "is_trained": self.is_trained,
            "last_updated": date.today().isoformat(),
            "sklearn_checksum": sklearn_checksum,
            "model_weights": self.weights,  # Persist dynamic weights
        }
        with open(f"{base_path}_meta.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Ensemble model saved (hybrid) to {base_path} with checksum {sklearn_checksum[:8]}"
        )

    def load_model(self, filepath: str):
        """Model parametrelerini yükle (Güvenli SHA256 Doğrulamalı)"""
        import json

        import joblib

        base_path = Path(filepath).with_suffix("")

        # 1. Metadata yükle
        meta_file = Path(f"{base_path}_meta.json")
        if not meta_file.exists():
            raise FileNotFoundError(f"Metadata dosyası bulunamadı: {meta_file}")

        with open(meta_file, encoding="utf-8") as f:
            metadata = json.load(f)

        self.physics_weight = metadata["physics_weight"]
        self.training_stats = metadata["training_stats"]
        self.is_trained = metadata["is_trained"]
        self.weights = metadata.get(
            "model_weights", self.DEFAULT_WEIGHTS.copy()
        )  # Load weights
        expected_checksum = metadata.get("sklearn_checksum")

        # 2. Sklearn modelleri yükle (GÜVENLİK KRİTİK: Checksum doğrulaması)
        sklearn_file = Path(f"{base_path}_sklearn.joblib")
        if sklearn_file.exists():
            # Checksum doğrula
            if expected_checksum:
                actual_checksum = self._calculate_checksum(str(sklearn_file))
                if actual_checksum != expected_checksum:
                    logger.error(
                        f"GÜVENLİK İHLALİ: Model dosyası checksum uyuşmazlığı! {sklearn_file}. Expected: {expected_checksum}, Actual: {actual_checksum}"
                    )
                    raise SecurityError(
                        "Model dosyası bozulmuş veya değiştirilmiş olabilir!"
                    )
            else:
                logger.warning(
                    f"Model yüklendi ancak checksum doğrulaması yapılamadı (metadata eksik): {sklearn_file}"
                )

            # joblib.load öncesi dosya boyutu kontrolü (DoS protection için çok büyük dosya engelleme)
            if sklearn_file.stat().st_size > 100 * 1024 * 1024:  # 100MB limit
                logger.error(
                    f"Güvenlik uyarısı: Model dosyası çok büyük! {sklearn_file}"
                )
                raise SecurityError(
                    "Model dosyası kabul edilebilir boyut limitini aşıyor."
                )

            sklearn_data = joblib.load(sklearn_file)
            self.gb_model = sklearn_data.get("gb_model", self.gb_model)
            self.rf_model = sklearn_data.get("rf_model", self.rf_model)
            self.xgb_model = sklearn_data.get("xgb_model", self.xgb_model)
            self.lgb_model = sklearn_data.get("lgb_model", self.lgb_model)
            self.scaler = sklearn_data.get("scaler", self.scaler)
            logger.debug(f"Sklearn models loaded and verified: {sklearn_file}")

        # 3. Native Modelleri yükle (JSON formatı doğal olarak daha güvenlidir)
        if XGBOOST_AVAILABLE and self.xgb_model is None:
            xgb_file = Path(f"{base_path}_xgb.json")
            if xgb_file.exists():
                import xgboost as xgb_lib

                self.xgb_model = xgb_lib.XGBRegressor()
                self.xgb_model.load_model(str(xgb_file))

        if LIGHTGBM_AVAILABLE and self.lgb_model is None:
            lgb_file = Path(f"{base_path}_lgb.json")
            if lgb_file.exists():
                import lightgbm as lgb_lib

                self.lgb_model = lgb_lib.LGBMRegressor()
                # If we are here, we are using the native JSON fallback
                # This part is more complex for LGBMRegressor wrapper,
                # but joblib above should have handled it in most cases.
                booster = lgb_lib.Booster(model_file=str(lgb_file))
                self.lgb_model._Booster = booster

        logger.info(f"Ensemble model loaded and verified from {base_path}")
        return {"success": True}


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

            # Diskten yüklemeyi dene (Persistence Fix)
            try:
                model_dir = Path("app/models")
                model_path = model_dir / f"ensemble_v2_{arac_id}.pkl"
                # Meta dosyası varlığı en güvenilir kontrol (joblib + json hibrit yapısı)
                if (model_dir / f"ensemble_v2_{arac_id}_meta.json").exists():
                    predictor.load_model(str(model_path))
                    logger.info(
                        f"Loaded existing model for vehicle {arac_id} from disk."
                    )
            except Exception as e:
                logger.debug(
                    f"No existing persistent model for vehicle {arac_id} or load failed: {e}"
                )

            self.predictors[arac_id] = predictor

            # Limit aşılırsa en eskiyi (baştakini) çıkar
            if len(self.predictors) > self.MAX_PREDICTORS:
                oldest_id, _ = self.predictors.popitem(last=False)
                logger.debug(
                    f"LRU Cache: Arac {oldest_id} predictor bellekten temizlendi."
                )

            return predictor

    def _calculate_training_hash(self, seferler: List[Dict]) -> str:
        """
        Gelişmiş Eğitim Verisi Parmak İzi (Stratified & Statistical)
        Sadece ID değil, mesafe ve yük dağılımını da kapsar.
        """
        import hashlib
        import json

        if not seferler:
            return "empty"

        # 1. Örneklem ID'leri (ilk 100)
        sample_ids = [str(s.get("id", i)) for i, s in enumerate(seferler[:100])]

        # 2. İstatistiksel özet (Data Drift yakalamak için)
        distances = [float(s.get("mesafe_km", 0) or 0) for s in seferler]
        loads = [float(s.get("ton", 0) or 0) for s in seferler]

        stats_fingerprint = {
            "count": len(seferler),
            "mean_dist": round(np.mean(distances), 1) if distances else 0,
            "mean_load": round(np.mean(loads), 1) if loads else 0,
            "ids_hash": hashlib.md5(",".join(sample_ids).encode()).hexdigest()[:8],
        }

        return hashlib.sha256(
            json.dumps(stats_fingerprint, sort_keys=True).encode()
        ).hexdigest()[:16]

    async def train_for_vehicle(
        self, arac_id: int, include_synthetic: bool = False
    ) -> Dict:
        """
        Belirli araç için model eğit.
        Veritabanından verileri toplar ve enrich eder.
        """
        from app.core.services.sofor_analiz_service import get_sofor_analiz_service
        from app.core.services.weather_service import get_weather_service

        # Araç bilgisini al
        arac = await self.arac_repo.get_by_id(arac_id)
        if not arac:
            return {"success": False, "error": "Araç bulunamadı"}

        # Araç yaşı ve faktörü hesapla
        from app.core.entities.models import Arac

        arac_entity = Arac(**arac)
        arac_yasi = arac_entity.yas
        yas_faktoru = arac_entity.yas_faktoru

        # Eğitim verilerini al
        seferler = await self.sefer_repo.get_for_training(
            arac_id, limit=500, include_synthetic=include_synthetic
        )
        if len(seferler) < 10:
            return {"success": False, "error": f"Yetersiz veri: {len(seferler)} sefer"}

        # Verileri enrich et
        weather_service = get_weather_service()
        sofor_service = get_sofor_analiz_service()

        # Optimized: Bulk fetch driver stats Once (Phase 2G Optimization)
        # Using include_elite_score=False to prevent QueuePool exhaustion (Phase 2G Fix)
        all_driver_stats = await sofor_service.get_driver_stats(
            include_elite_score=False
        )
        driver_map = {d.sofor_id: d for d in all_driver_stats}

        enriched_seferler = []
        y_values = []

        for s in seferler:
            # Mevsim faktörü
            target_date = date.today()  # Varsayılan
            mevsim_faktor = weather_service.get_seasonal_factor(target_date)

            # Şoför faktörü (varsa) - Using lookup map instead of API call
            sofor_katsayi = 1.0
            sid = s.get("sofor_id")
            if sid and sid in driver_map:
                driver = driver_map[sid]
                # Filo karşılaştırmadan şoför katsayısı
                sofor_katsayi = 1.0 - (driver.filo_karsilastirma / 100) * 0.1

            enriched = {
                **s,
                "arac_yasi": arac_yasi,
                "yas_faktoru": yas_faktoru,
                "mevsim_faktor": mevsim_faktor,
                "sofor_katsayi": sofor_katsayi,
            }

            enriched_seferler.append(enriched)
            y_values.append(float(s["tuketim"]))

        # Model eğit
        predictor = self.get_predictor(arac_id)
        result = predictor.fit(enriched_seferler, np.array(y_values))

        if result["success"]:
            logger.info(f"Ensemble model trained for vehicle {arac_id}: {result}")

            # 1. ModelManager ile Versiyonlama (Elite)
            try:
                from app.core.ml.model_manager import get_model_manager, ModelType

                manager = get_model_manager()

                # En iyi R2 skorunu bul
                # Phase 5A: Metrics are nested in 'metrics' dictionary
                m = result.get("metrics", {})
                r2_scores = [
                    result.get("ensemble_r2"),
                    m.get("gb_test_r2"),
                    m.get("rf_test_r2"),
                    m.get("xgb_test_r2"),
                    m.get("lgb_test_r2"),
                    m.get("gb_cv_mean"),
                ]
                valid_scores = [float(s) for s in r2_scores if s is not None]
                best_r2 = max(valid_scores) if valid_scores else 0.0

                metrics = {
                    "r2_score": best_r2,
                    "mae": result.get("physics_mae"),
                    "sample_count": result.get("sample_count"),
                }

                manager.save_version(
                    arac_id=arac_id,
                    model_type=ModelType.ENSEMBLE,
                    params=result,
                    metrics=metrics,
                    notes="Auto-trained via EnsembleService (Phase 5 Elite)",
                    feature_schema_hash=self._feature_hash,
                    training_data_hash=self._calculate_training_hash(seferler),
                    physics_version=self._physics_version,
                )
                logger.info(f"Model version saved for vehicle {arac_id}")
            except Exception as e:
                logger.error(f"Failed to save model version: {e}")

            # 2. AnalizRepo ile Legacy Kayıt (YakitFormul)
            try:
                from app.database.repositories.analiz_repo import get_analiz_repo

                analiz_repo = get_analiz_repo()
                await analiz_repo.save_model_params(arac_id, result)
                logger.info(f"Legacy model params saved for vehicle {arac_id}")
            except Exception as e:
                logger.error(f"Failed to save legacy model params: {e}")

            # 3. Serialize Model to Disk (Persistence fix for Elite Benchmark)
            try:
                model_dir = Path("app/models")
                model_dir.mkdir(parents=True, exist_ok=True)
                model_path = model_dir / f"ensemble_v2_{arac_id}.pkl"

                # Save the trained model
                predictor.save_model(str(model_path))
                logger.info(f"Serialized ensemble model saved for vehicle {arac_id}")
            except Exception as e:
                logger.error(f"Failed to serialize model for vehicle {arac_id}: {e}")

        return result

    async def train_general_model(self, include_synthetic: bool = False) -> Dict:
        """
        Tüm araçların verilerini kullanarak GENEL bir model eğitir (Fallback Modeli).
        Araç ID = 0 olarak kaydedilir.
        """
        logger.info(
            f"Training General Fallback Model (Vehicle ID: 0, Synthetic: {include_synthetic})..."
        )
        try:
            from app.database.repositories.analiz_repo import get_analiz_repo

            analiz_repo = get_analiz_repo()

            is_real_filter = "AND s.is_real = TRUE" if not include_synthetic else ""

            # 1. Tüm tamamlanmış seferleri çek
            # Not: Repository limitini 2000'e çıkarıyoruz (Genel model için daha çok veri)
            query = f"""
                SELECT 
                    s.mesafe_km,
                    s.net_kg / 1000.0 as ton,
                    s.tuketim,
                    s.sofor_id,
                    l.ascent_m,
                    l.zorluk,
                    s.rota_detay
                FROM seferler s
                LEFT JOIN lokasyonlar l ON (s.cikis_yeri = l.cikis_yeri AND s.varis_yeri = l.varis_yeri)
                WHERE s.tuketim IS NOT NULL 
                  AND s.tuketim > 0
                  AND s.durum = 'Tamam'
                  {is_real_filter}
                ORDER BY s.tarih DESC
                LIMIT 2000
            """
            seferler = await analiz_repo.execute_query(query)

            if len(seferler) < 20:
                return {
                    "success": False,
                    "error": f"Yetersiz toplam veri: {len(seferler)}",
                }

            # 2. Modeli eğit
            y_actual = np.array([float(s["tuketim"]) for s in seferler])
            predictor = self.get_predictor(0)  # General model key
            result = predictor.fit(seferler, y_actual)

            if result.get("success"):
                # 3. Kaydet
                from app.core.ml.model_manager import get_model_manager, ModelType

                manager = get_model_manager()

                metrics = {
                    "r2": result.get("gb_test_r2"),
                    "mae": result.get("physics_mae"),
                    "sample_count": result.get("sample_count"),
                }

                manager.save_version(
                    arac_id=0,
                    model_type=ModelType.ENSEMBLE,
                    params=result,
                    metrics=metrics,
                    notes="General Fallback Model (All vehicles) - Phase 5 Elite",
                    feature_schema_hash=self._feature_hash,
                    training_data_hash=self._calculate_training_hash(seferler),
                    physics_version=self._physics_version,
                )
                await analiz_repo.save_model_params(0, result)

                # 4. Serialize General Model to Disk
                try:
                    model_dir = Path("app/models")
                    model_dir.mkdir(parents=True, exist_ok=True)
                    model_path = model_dir / "ensemble_v2_0.pkl"
                    predictor.save_model(str(model_path))
                    logger.info("Serialized General Fallback Model saved to disk.")
                except Exception as e:
                    logger.error(f"Failed to serialize general model: {e}")

                logger.info("General Fallback Model trained and saved successfully.")

            return result
        except Exception as e:
            logger.error(f"General model training failed: {e}")
            return {"success": False, "error": str(e)}

    async def predict_consumption(
        self,
        arac_id: int,
        mesafe_km: float,
        ton: float,
        sofor_id: Optional[int] = None,
        ascent_m: float = 0,
        descent_m: float = 0,
        dorse_id: Optional[int] = None,
        target_date: Optional[date] = None,
        is_empty_trip: bool = False,
        uow=None,  # Optimization for session reuse
        route_analysis: Optional[Dict] = None,  # Phase 8
    ) -> Dict:
        """
        Yakıt tüketimi tahmin et
        """
        from app.core.services.sofor_analiz_service import get_sofor_analiz_service
        from app.core.services.weather_service import get_weather_service

        # Single Session Reuse Pattern (Phase 3 Optimization)
        if uow:
            arac = await uow.arac_repo.get_by_id(arac_id)
        else:
            arac = await self.arac_repo.get_by_id(arac_id)

        if not arac:
            return {"success": False, "error": "Araç bulunamadı"}

        # Dorse verisi (Phase 4)
        dorse = None
        if dorse_id:
            if uow:
                dorse = await uow.dorse_repo.get_by_id(dorse_id)
            else:
                dorse = await self.dorse_repo.get_by_id(dorse_id)

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
            # Pass 'uow' for session consistency (Phase 3 Optimization)
            stats = await sofor_service.get_driver_stats(
                sofor_id, include_elite_score=False, uow=uow
            )
            if stats:
                sofor_katsayi = 1.0 - (stats[0].filo_karsilastirma / 100) * 0.1

        sefer = {
            "mesafe_km": mesafe_km,
            "ton": ton,
            "ascent_m": ascent_m,
            "descent_m": descent_m,
            "arac_yasi": arac_entity.yas,
            "yas_faktoru": arac_entity.yas_faktoru,
            "mevsim_faktor": mevsim_faktor,
            "sofor_katsayi": sofor_katsayi,
            "is_empty_trip": is_empty_trip,
            "dorse_bos_agirlik": dorse.get("bos_agirlik_kg") if dorse else 6500.0,
            "dorse_lastik_sayisi": dorse.get("lastik_sayisi") if dorse else 6,
            "dorse_lastik_direnci": dorse.get("dorse_lastik_direnc_katsayisi")
            if dorse
            else 0.006,
            "dorse_hava_direnci": dorse.get("dorse_hava_direnci") if dorse else 0.13,
            "rota_detay": {"route_analysis": route_analysis}
            if route_analysis
            else None,
        }

        predictor = self.get_predictor(arac_id)

        # Phase 4 Elite: Fallback to General Model (ID 0) if vehicle-specific is not trained
        if not predictor.is_trained and arac_id != 0:
            logger.info(
                f"Vehicle {arac_id} model not trained. Using General Model (ID 0) fallback."
            )
            predictor = self.get_predictor(0)

        result = predictor.predict(sefer)

        return {
            "success": True,
            "tahmin_l_100km": result.tahmin_l_100km,
            "tahmin_litre": round(mesafe_km * result.tahmin_l_100km / 100, 1),
            "guven_araligi": (result.confidence_low, result.confidence_high),
            "physics_only": result.physics_only,
            "ml_correction": result.ml_correction,
            "factors": {
                "arac_yasi": arac_entity.yas,
                "yas_faktoru": round(arac_entity.yas_faktoru, 3),
                "euro_sinifi": arac_entity.euro_sinifi,
                "mevsim_faktor": mevsim_faktor,
                "sofor_katsayi": round(sofor_katsayi, 3),
            },
        }

    async def predict_batch(self, requests: List[Dict]) -> List[Dict]:
        """
        Gelişmiş N+1 Fix: Tek session ile toplu tahmin (Phase 3)
        """
        from app.database.unit_of_work import UnitOfWork

        results = []
        async with UnitOfWork() as uow:
            for req in requests:
                res = await self.predict_consumption(uow=uow, **req)
                results.append(res)
        return results


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
