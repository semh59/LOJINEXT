"""
ELITE Yakıt Tahmin Servisi
Fizik tabanlı modeller ve XGBoost Ensemble mimarisini birleştirir.
"""

import asyncio
import threading
from datetime import date
from typing import Dict, Optional

from app.config import settings
from app.core.ml.ensemble_predictor import get_ensemble_service
from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    RouteConditions,
    VehicleSpecs,
)
from app.core.services.weather_service import get_weather_service
from app.database.unit_of_work import get_uow
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class PredictionService:
    """
    ELITE Yakıt Tahmin Servisi.

    Hibrit yaklaşım:
    1. Fizik tabanlı model (PIML) - araca özel spekler
    2. Hava durumu faktörü
    3. Şoför performans katsayısı
    4. Ensemble (ML) düzeltmesi
    """

    def __init__(self, db=None):
        self.db = db
        self.physics_predictor = PhysicsBasedFuelPredictor()
        self.ensemble_service = get_ensemble_service()
        self.weather_service = get_weather_service()

        # Lazy initialization to avoid circular dependency
        self._yakit_tahmin_service = None

    @property
    def yakit_tahmin_service(self):
        """Lazy load yakit_tahmin_service to avoid circular dependency"""
        if self._yakit_tahmin_service is None:
            from app.core.services.yakit_tahmin_service import get_yakit_tahmin_service
            self._yakit_tahmin_service = get_yakit_tahmin_service()
        return self._yakit_tahmin_service

    async def predict_consumption(
        self,
        arac_id: int,
        mesafe_km: float,
        ton: float,
        ascent_m: float = 0,
        descent_m: float = 0,
        ramp_pct: Optional[float] = None,
        sofor_id: Optional[int] = None,
        target_date: Optional[date] = None,
        use_ensemble: bool = True,
    ) -> Dict:
        """
        Gelişmiş yakıt tahmini yapar (Elite).

        Args:
            arac_id: Araç ID
            mesafe_km: Toplam mesafe
            ton: Yük ağırlığı
            ascent_m: Toplam tırmanış
            descent_m: Toplam iniş
            ramp_pct: Rampa yüzdesi
            sofor_id: Şoför ID (opsiyonel)
            target_date: Hedef tarih (opsiyonel)
            use_ensemble: ML ensemble kullanılsın mı

        Returns:
            Dict: Tahmin sonuçları
        """
        target_date = target_date or date.today()

        # 0. Veritabanından Teknik Spekleri Çek
        async with get_uow() as uow:
            arac = await uow.arac_repo.get_by_id(arac_id)
            sofor = None
            if sofor_id:
                sofor = await uow.sofor_repo.get_by_id(sofor_id)

        # Araç varsa teknik spekleri ata, yoksa default
        specs = VehicleSpecs()
        if arac:
            specs = VehicleSpecs(
                empty_weight_kg=arac.get("bos_agirlik_kg", 8000.0),
                drag_coefficient=arac.get("hava_direnc_katsayisi", 0.7),
                frontal_area_m2=arac.get("on_kesit_alani_m2", 8.5),
                engine_efficiency=arac.get("motor_verimliligi", 0.38),
                rolling_resistance=arac.get("lastik_direnc_katsayisi", 0.007),
            )

            # Yaş degradasyonu (config-driven)
            yas = arac.get("yil", 2020)
            current_year = date.today().year
            age = max(0, current_year - yas)

            if age > 5:
                degradation_rate = settings.VEHICLE_AGE_DEGRADATION_RATE
                max_degradation = settings.MAX_AGE_DEGRADATION
                age_factor = max(1.0 - max_degradation, 1.0 - (age * degradation_rate))
                specs.engine_efficiency *= age_factor

        # 1. Hava Durumu Faktörü
        weather_factor = await asyncio.to_thread(
            self.weather_service.get_seasonal_factor, target_date
        )

        # 2. Fizik Tabanlı Tahmin (Araca Özel Specs ile)
        predictor = PhysicsBasedFuelPredictor(specs)
        route = RouteConditions(
            distance_km=mesafe_km,
            load_ton=ton,
            ascent_m=ascent_m,
            descent_m=descent_m,
            weather_factor=weather_factor,
        )

        # CPU-bound fizik motoru hesaplaması
        physics_result = await asyncio.to_thread(predictor.predict, route)
        current_l_100km = physics_result.consumption_l_100km

        # 3. AI Kalibrasyon Kaydı (Background Task)
        await self._log_prediction_to_ai(arac_id, mesafe_km, current_l_100km)

        # 4. Şoför ve Rampa Düzeltmeleri
        if sofor:
            score = (
                sofor.get("score", 1.0) if isinstance(sofor, dict) else getattr(sofor, "score", 1.0)
            )
            # DOĞRU MANTIK: Puan yükseldikçe (iyileştikçe) yakıt çarpanı düşer.
            # 1.0 = Nötr, 2.0 = 0.8x (Mükemmel), 0.1 = 1.2x (Kötü)
            # Lineer Mapping: multiplier = 1.0 + (1.0 - score) * 0.2
            sofor_influence = 1.0 + (1.0 - score) * 0.2
            sofor_influence = max(0.8, min(1.2, sofor_influence))
            current_l_100km *= sofor_influence

        if ramp_pct is not None:
            # Config-driven rampa faktörü
            ramp_coefficient = 0.2  # TODO: settings.RAMP_FACTOR_COEFFICIENT
            ramp_factor = 1.0 + (ramp_pct / 100) * ramp_coefficient
            current_l_100km *= ramp_factor

        # 5. Ensemble (ML) Düzeltmesi
        if use_ensemble and arac_id > 0:
            try:
                ensemble_result = await self.ensemble_service.predict_consumption(
                    arac_id=arac_id,
                    mesafe_km=mesafe_km,
                    ton=ton,
                    sofor_id=sofor_id,
                    ascent_m=ascent_m,
                    descent_m=descent_m,
                    target_date=target_date,
                )

                if ensemble_result.get("success"):
                    return {
                        "prediction_l_100km": round(ensemble_result["tahmin_l_100km"], 2),
                        "prediction_liters": round(
                            mesafe_km * ensemble_result["tahmin_l_100km"] / 100, 1
                        ),
                        "confidence_range": ensemble_result["guven_araligi"],
                        "physics_base": physics_result.consumption_l_100km,
                        "ml_correction": ensemble_result["ml_correction"],
                        "weather_factor": weather_factor,
                        "method": "Ensemble (Elite Hybrid)",
                    }
            except Exception as e:
                logger.warning(f"Ensemble prediction failed, falling back to Physics: {e}")

        # Fallback to Physics Only
        return {
            "prediction_l_100km": round(current_l_100km, 2),
            "prediction_liters": round(mesafe_km * current_l_100km / 100, 1),
            "confidence_range": physics_result.confidence_range,
            "physics_base": physics_result.consumption_l_100km,
            "weather_factor": weather_factor,
            "method": "Physics-Only (Elite Dynamic)",
        }

    async def _log_prediction_to_ai(self, arac_id: int, mesafe_km: float, consumption: float):
        """Background task: AI'a tahmin bilgisi gönder"""
        try:
            from app.services.smart_ai_service import get_smart_ai

            smart_ai = get_smart_ai()

            async def _safe_teach():
                try:
                    await smart_ai.teach(
                        f"Tahmin: Araç {arac_id}, {mesafe_km} km, {consumption:.2f} L/100km",
                        category="tahmin_izleme",
                    )
                except Exception as e:
                    logger.debug(f"AI teach task failed (non-critical): {e}")

            asyncio.create_task(_safe_teach())
        except Exception:
            pass  # AI unavailable, silent fail

    async def train_model(self, arac_id: int) -> Dict:
        """Belirli bir araç için tüm modelleri (Ensemble) eğitir."""
        return await self.ensemble_service.train_for_vehicle(arac_id)

    async def train_linear_model(self, arac_id: int) -> Dict:
        """Sadece Linear Regression modelini eğitir."""
        res = await self.yakit_tahmin_service.train_model(arac_id)
        if res.get("success"):
            return {"status": "success", "model_type": "linear", **res}
        return {"status": "error", "message": res.get("error", "Eğitim hatası")}

    async def train_xgboost_model(self, arac_id: int) -> Dict:
        """Sadece XGBoost/Ensemble modelini eğitir."""
        res = await self.ensemble_service.train_for_vehicle(arac_id)
        if res.get("success"):
            return {"status": "success", "model_type": "ensemble", **res}
        return {"status": "error", "message": res.get("error", "Eğitim hatası")}


# Thread-safe Singleton
_prediction_service: Optional[PredictionService] = None
_prediction_service_lock = threading.Lock()


def get_prediction_service() -> PredictionService:
    """Thread-safe singleton getter"""
    global _prediction_service
    if _prediction_service is None:
        with _prediction_service_lock:
            if _prediction_service is None:
                _prediction_service = PredictionService()
    return _prediction_service
