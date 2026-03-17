import asyncio
import logging
from datetime import date
from typing import Any, Dict, Optional

from app.config import settings
from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    RouteConditions,
    VehicleSpecs,
)
from app.database.unit_of_work import UnitOfWork
from app.core.ml.ensemble_predictor import get_ensemble_service
from app.core.services.weather_service import WeatherService
from app.core.services.yakit_tahmin_service import YakitTahminService

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Yakıt Tahmin Servisi.
    Fizik motoru ve ML modellerini (Ensemble) orkestra eder.
    """

    def __init__(self):
        self.weather_service = WeatherService()
        self.yakit_tahmin_service = YakitTahminService()
        self.ensemble_service = get_ensemble_service()

    @staticmethod
    def _build_explanation_summary(
        model_used: str,
        model_version: str,
        confidence_score: float,
        load_ton: float,
        ascent_m: float,
        weather_factor: float,
    ) -> str:
        return (
            f"{model_used}/{model_version} ile tahmin yapildi. "
            f"Guven skoru: {confidence_score:.2f}. "
            f"Yuk: {load_ton:.1f} ton, tirmanis: {ascent_m:.0f} m, "
            f"hava etkisi: {weather_factor:.2f}."
        )

    @staticmethod
    def _normalize_confidence_band(
        base_value: float,
        confidence_score: float,
        confidence_low: Optional[float] = None,
        confidence_high: Optional[float] = None,
    ) -> tuple[float, float]:
        if confidence_low is not None and confidence_high is not None:
            return round(float(confidence_low), 2), round(float(confidence_high), 2)

        spread_ratio = max(0.06, min(0.30, 0.30 - (confidence_score * 0.2)))
        low = max(0.0, base_value * (1 - spread_ratio))
        high = base_value * (1 + spread_ratio)
        return round(low, 2), round(high, 2)

    def _build_prediction_response(
        self,
        *,
        mesafe_km: float,
        tahmini_tuketim: float,
        model_used: str,
        model_version: str,
        confidence_score: float,
        warning_level: str,
        fallback_triggered: bool,
        faktorler: Dict[str, Any],
        insight: Optional[str] = None,
        confidence_low: Optional[float] = None,
        confidence_high: Optional[float] = None,
        explanation_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        tahmini_tuketim = round(float(tahmini_tuketim), 2)
        tahmini_litre = round(float(mesafe_km) * tahmini_tuketim / 100, 1)
        confidence_score = round(float(confidence_score), 2)
        c_low, c_high = self._normalize_confidence_band(
            base_value=tahmini_tuketim,
            confidence_score=confidence_score,
            confidence_low=confidence_low,
            confidence_high=confidence_high,
        )

        payload = {
            "tahmini_tuketim": tahmini_tuketim,
            "tahmini_litre": tahmini_litre,
            # Deprecated alias for transition period.
            "prediction_liters": tahmini_litre,
            "model_used": model_used,
            "model_version": model_version,
            "status": "success",
            "confidence_score": confidence_score,
            "confidence_low": c_low,
            "confidence_high": c_high,
            "warning_level": warning_level,
            "fallback_triggered": bool(fallback_triggered),
            "faktorler": faktorler,
            "explanation_summary": explanation_summary
            or "Tahmin tamamlandi, teknik detaylar faktorlerde listelendi.",
            "insight": insight,
        }
        return payload

    async def predict_consumption(
        self,
        arac_id: int,
        mesafe_km: float,
        ton: float = 0.0,
        ascent_m: float = 0.0,
        descent_m: float = 0.0,
        flat_distance_km: float = 0.0,
        sofor_id: Optional[int] = None,
        dorse_id: Optional[int] = None,
        sofor_score: Optional[float] = None,
        ramp_pct: Optional[float] = None,
        target_date: Optional[date] = None,
        zorluk: str = "Normal",
        use_ensemble: bool = True,
        bos_sefer: bool = False,
        route_analysis: Optional[Dict] = None,
    ) -> Dict:
        """
        Gelişmiş yakıt tahmini.
        1. Araç specs ve yaş düzeltmesi.
        2. Hava durumu faktörü.
        3. Fizik motoru (Physics-based).
        4. ML Ensemble düzeltmesi (XGBoost + GB + RF + LightGBM).
        5. Şoför bazlı ince ayar.
        """
        if not target_date:
            target_date = date.today()

        # Araç ve Şoför verilerini çek
        arac = None
        sofor = None
        dorse = None
        async with UnitOfWork() as uow:
            # Pydantic schema expects int, so ensure we have int
            if arac_id > 0:
                arac_data = await uow.arac_repo.get_by_id(arac_id)
                if arac_data:
                    # Convert model instance to dict if necessary
                    arac = (
                        arac_data.__dict__
                        if hasattr(arac_data, "__dict__")
                        else arac_data
                    )

                if sofor_id:
                    sofor_data = await uow.sofor_repo.get_by_id(sofor_id)
                    if sofor_data:
                        sofor = (
                            sofor_data.__dict__
                            if hasattr(sofor_data, "__dict__")
                            else sofor_data
                        )

                if dorse_id:
                    dorse_data = await uow.dorse_repo.get_by_id(dorse_id)
                    if dorse_data:
                        dorse = (
                            dorse_data.__dict__
                            if hasattr(dorse_data, "__dict__")
                            else dorse_data
                        )

        # Araç varsa teknik spekleri ata, yoksa default
        specs = VehicleSpecs()
        age = 0
        if arac:
            # Combo specs: Tractor from Arac, Trailer from Dorse
            specs = VehicleSpecs(
                empty_weight_kg=arac.get("bos_agirlik_kg", 8000.0),
                drag_coefficient=arac.get("hava_direnc_katsayisi", 0.52),
                frontal_area_m2=arac.get("on_kesit_alani_m2", 8.5),
                engine_efficiency=arac.get("motor_verimliligi", 0.38),
                rolling_resistance=arac.get("lastik_direnc_katsayisi", 0.007),
            )

            if dorse:
                specs.trailer_empty_weight_kg = dorse.get("bos_agirlik_kg", 6500.0)
                specs.trailer_rolling_resistance = dorse.get(
                    "dorse_lastik_direnc_katsayisi", 0.006
                )
                specs.trailer_drag_contribution = dorse.get("dorse_hava_direnci", 0.13)

            # Yaş degradasyonu (config-driven)
            yas = arac.get("yil", 2020)
            current_year = date.today().year
            age = max(0, current_year - yas)

            if age > 5:
                degradation_rate = settings.VEHICLE_AGE_DEGRADATION_RATE
                max_degradation = settings.MAX_AGE_DEGRADATION
                age_factor = max(1.0 - max_degradation, 1.0 - (age * degradation_rate))
                specs.engine_efficiency *= age_factor

        otoyol_ratio = 0.6
        devlet_yolu_ratio = 0.3
        sehir_ici_ratio = 0.1
        if route_analysis and "ratios" in route_analysis:
            ratios = route_analysis["ratios"]
            otoyol_ratio = ratios.get("otoyol", 0.6)
            devlet_yolu_ratio = ratios.get("devlet_yolu", 0.3)
            sehir_ici_ratio = ratios.get("sehir_ici", 0.1)

        # 1. Hava Durumu Faktörü
        if route_analysis and "weather_factor" in route_analysis:
            weather_factor = float(route_analysis["weather_factor"])
        else:
            weather_factor = await asyncio.to_thread(
                self.weather_service.get_seasonal_factor, target_date
            )

        predictor = PhysicsBasedFuelPredictor(specs)

        # Phase 12: Dynamic Insight Stats
        historical_stats = (
            route_analysis.get("historical_stats") if route_analysis else None
        )

        # 3. Check for Granular Geometry (Phase 11 P2P)
        granular_nodes = (
            route_analysis.get("granular_nodes") if route_analysis else None
        )

        if granular_nodes:
            logger.info(
                f"Using High-Fidelity P2P Physics ({len(granular_nodes)} nodes)"
            )
            physics_result = await asyncio.to_thread(
                predictor.predict_granular,
                granular_nodes,
                ton,
                bos_sefer,
                historical_stats=historical_stats,
                arac_yasi=age,
            )
        else:
            # Fallback to Summary-based Physics (using legacy wrapper)
            route = RouteConditions(
                distance_km=mesafe_km,
                load_ton=0.0 if bos_sefer else ton,
                is_empty_trip=bos_sefer,
                ascent_m=ascent_m,
                descent_m=descent_m,
                flat_distance_km=flat_distance_km,
                weather_factor=weather_factor,
                otoyol_ratio=otoyol_ratio,
                devlet_yolu_ratio=devlet_yolu_ratio,
                sehir_ici_ratio=sehir_ici_ratio,
                arac_yasi=age,
            )
            physics_result = await asyncio.to_thread(
                predictor.predict, route, historical_stats=historical_stats
            )

        current_l_100km = physics_result.consumption_l_100km

        # 3. AI Kalibrasyon Kaydı (Background Task)
        await self._log_prediction_to_ai(arac_id, mesafe_km, current_l_100km)

        # 4. Sofor ve Rampa Duzeltmeleri
        s_score = sofor_score
        if s_score is None and sofor:
            s_score = sofor.get("score", 1.0)

        if s_score is not None:
            sofor_influence = 1.0 + (1.0 - s_score) * 0.2
            sofor_influence = max(0.8, min(1.2, sofor_influence))
            current_l_100km *= sofor_influence
        else:
            sofor_influence = 1.0

        if ramp_pct is not None:
            ramp_coefficient = 0.2
            ramp_factor = 1.0 + (ramp_pct / 100) * ramp_coefficient
            current_l_100km *= ramp_factor
        else:
            ramp_factor = 1.0

        base_factors = {
            "physics_base": round(physics_result.consumption_l_100km, 2),
            "weather_factor": round(weather_factor, 2),
            "sofor_score": round(float(s_score or 1.0), 2),
            "driver_factor": round(sofor_influence, 3),
            "ramp_factor": round(ramp_factor, 3),
            "load_ton": round(float(0.0 if bos_sefer else ton), 2),
            "ascent_m": round(float(ascent_m or 0.0), 1),
            "descent_m": round(float(descent_m or 0.0), 1),
            "flat_distance_km": round(float(flat_distance_km or 0.0), 2),
            "otoyol_ratio": round(float(otoyol_ratio), 3),
            "devlet_yolu_ratio": round(float(devlet_yolu_ratio), 3),
            "sehir_ici_ratio": round(float(sehir_ici_ratio), 3),
            "vehicle_age": age,
            "has_trailer": 1.0 if dorse_id else 0.0,
            "difficulty_level": zorluk,
        }

        # 5. Ensemble (ML) Duzeltmesi
        if use_ensemble and arac_id > 0:
            try:
                # ensemble_service uses its own uow internally if not provided, but we can pass it
                async with UnitOfWork() as uow_ensemble:
                    ensemble_result = await self.ensemble_service.predict_consumption(
                        arac_id=arac_id,
                        mesafe_km=mesafe_km,
                        ton=ton,
                        sofor_id=sofor_id,
                        dorse_id=dorse_id,
                        ascent_m=ascent_m,
                        descent_m=descent_m,
                        target_date=target_date,
                        is_empty_trip=bos_sefer,
                        uow=uow_ensemble,
                        route_analysis=route_analysis,
                    )

                if ensemble_result.get("success"):
                    tahmin_l_100km = ensemble_result["tahmin_l_100km"]
                    confidence = ensemble_result.get("confidence_score", 1.0)

                    warning_level = "GREEN"
                    fallback_triggered = False

                    threshold_red = getattr(
                        settings, "AI_CONFIDENCE_THRESHOLD_RED", 0.40
                    )
                    threshold_yellow = getattr(
                        settings, "AI_CONFIDENCE_THRESHOLD_YELLOW", 0.60
                    )

                    if confidence < threshold_red:
                        warning_level = "RED"
                        tahmin_l_100km = current_l_100km
                        fallback_triggered = True
                        logger.warning(
                            f"AI Confidence RED ({confidence:.2f}). Physics fallback triggered."
                        )

                    elif confidence < threshold_yellow:
                        warning_level = "YELLOW"
                        logger.info(
                            f"AI Confidence YELLOW ({confidence:.2f}). Proceeding with caution."
                        )

                    factors = {
                        **base_factors,
                        "ml_correction": round(
                            float(ensemble_result.get("ml_correction", 0.0)), 2
                        )
                        if not fallback_triggered
                        else 0.0,
                        "champion_model": ensemble_result.get("champion", "ensemble"),
                        "challenger_model": ensemble_result.get(
                            "challenger", "physics"
                        ),
                    }

                    model_version = str(
                        ensemble_result.get("model_version", "ensemble-v2.0-champion")
                    )
                    explanation_summary = self._build_explanation_summary(
                        model_used="ensemble"
                        if not fallback_triggered
                        else "physics_fallback",
                        model_version=model_version,
                        confidence_score=float(confidence),
                        load_ton=float(0.0 if bos_sefer else ton),
                        ascent_m=float(ascent_m or 0.0),
                        weather_factor=float(weather_factor),
                    )

                    guven_araligi = ensemble_result.get("guven_araligi")
                    conf_low = (
                        guven_araligi[0]
                        if isinstance(guven_araligi, (list, tuple))
                        and len(guven_araligi) >= 2
                        else None
                    )
                    conf_high = (
                        guven_araligi[1]
                        if isinstance(guven_araligi, (list, tuple))
                        and len(guven_araligi) >= 2
                        else None
                    )

                    return self._build_prediction_response(
                        mesafe_km=mesafe_km,
                        tahmini_tuketim=tahmin_l_100km,
                        model_used="ensemble"
                        if not fallback_triggered
                        else "physics_fallback",
                        model_version=model_version,
                        confidence_score=float(confidence),
                        warning_level=warning_level,
                        fallback_triggered=fallback_triggered,
                        confidence_low=conf_low,
                        confidence_high=conf_high,
                        faktorler=factors,
                        insight=physics_result.insight,
                        explanation_summary=explanation_summary,
                    )
            except Exception as e:
                logger.warning(f"Ensemble prediction failed: {e}")

        # Fallback to Physics Only
        fallback_confidence = 0.72 if not use_ensemble else 0.55
        fallback_warning = "GREEN" if fallback_confidence >= 0.60 else "YELLOW"
        fallback_factors = {
            **base_factors,
            "ml_correction": 0.0,
            "fallback_reason": "ensemble_unavailable_or_disabled"
            if use_ensemble
            else "physics_mode_selected",
        }
        fallback_model = "physics" if use_ensemble else "linear"
        fallback_version = "physics-v2.0"
        fallback_summary = self._build_explanation_summary(
            model_used=fallback_model,
            model_version=fallback_version,
            confidence_score=fallback_confidence,
            load_ton=float(0.0 if bos_sefer else ton),
            ascent_m=float(ascent_m or 0.0),
            weather_factor=float(weather_factor),
        )
        return self._build_prediction_response(
            mesafe_km=mesafe_km,
            tahmini_tuketim=current_l_100km,
            model_used=fallback_model,
            model_version=fallback_version,
            confidence_score=fallback_confidence,
            warning_level=fallback_warning,
            fallback_triggered=bool(use_ensemble),
            faktorler=fallback_factors,
            insight=physics_result.insight,
            explanation_summary=fallback_summary,
        )

    async def _log_prediction_to_ai(
        self, arac_id: int, mesafe_km: float, consumption: float
    ):
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
                    logger.debug(f"AI teach task failed: {e}")

            asyncio.create_task(_safe_teach())
        except Exception:
            pass

    async def explain_consumption(
        self,
        arac_id: int,
        mesafe_km: float,
        ton: float = 0.0,
        ascent_m: float = 0.0,
        descent_m: float = 0.0,
        flat_distance_km: float = 0.0,
        sofor_id: Optional[int] = None,
        sofor_score: Optional[float] = None,
        zorluk: str = "Normal",
        route_analysis: Optional[Dict] = None,
    ) -> Dict:
        """
        Tahmin sonucunun nedenlerini açıklar (XAI).
        """
        # Feature setini hazırla (predict ile uyumlu)
        s_score = sofor_score
        if s_score is None and sofor_id:
            from app.core.services.sofor_analiz_service import get_sofor_analiz_service

            sofor_service = get_sofor_analiz_service()
            stats = await sofor_service.get_driver_stats(
                sofor_id, include_elite_score=False
            )
            if stats:
                s_score = 1.0 - (stats[0].filo_karsilastirma / 100) * 0.1

        sefer = {
            "mesafe_km": mesafe_km,
            "ton": ton,
            "ascent_m": ascent_m,
            "descent_m": descent_m,
            "flat_distance_km": flat_distance_km,
            "zorluk": zorluk,
            "sofor_id": sofor_id,
            "sofor_katsayi": s_score or 1.0,
            "route_analysis": route_analysis,
        }

        # Predictor al ve açıkla
        predictor = self.ensemble_service.get_predictor(arac_id)
        if not predictor.is_trained and arac_id != 0:
            predictor = self.ensemble_service.get_predictor(0)

        return await asyncio.to_thread(predictor.explain_prediction, sefer)

    async def train_xgboost_model(self, arac_id: int) -> Dict:
        """Belirli bir araç için tüm modelleri eğitir."""
        # ensemble_service uses train_for_vehicle method
        res = await self.ensemble_service.train_for_vehicle(arac_id)
        return {
            "status": "success" if res.get("success") else "failure",
            "model_type": "ensemble",
            "r2_score": res.get("r2", 0.0),
            "sample_count": res.get("samples", 0),
            "metrics": res.get("metrics", {}),
        }


# Singleton accessor
_prediction_service = None


def get_prediction_service() -> PredictionService:
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
