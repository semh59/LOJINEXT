"""
TIR Yakıt Takip - Gelişmiş Fizik Tabanlı Yakıt Tahmin Motoru
Enerji formülleri + ML hibrit yaklaşım
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VehicleSpecs:
    """Araç teknik özellikleri"""

    empty_weight_kg: float = 8000  # Tractor only (Standard)
    trailer_empty_weight_kg: float = 6500  # Trailer only (Standard)
    drag_coefficient: float = 0.52  # Tractor only Cd
    trailer_drag_contribution: float = 0.13  # Trailer contribution to Cd
    frontal_area_m2: float = 8.2
    rolling_resistance: float = 0.007
    trailer_rolling_resistance: float = 0.006
    engine_efficiency: float = 0.40
    fuel_density_kg_l: float = 0.835
    fuel_energy_mj_kg: float = 45.8

    def __post_init__(self):
        if self.engine_efficiency <= 0:
            raise ValueError("Engine efficiency must be greater than 0")
        if self.fuel_density_kg_l <= 0:
            raise ValueError("Fuel density must be greater than 0")


@dataclass
class RouteConditions:
    """Rota koşulları"""

    distance_km: float
    load_ton: float
    is_empty_trip: bool = False  # Faz 3: Boş sefer bayrağı
    ascent_m: float = 0  # Toplam tırmanış (metre)
    descent_m: float = 0  # Toplam iniş (metre)
    flat_distance_km: float = 0  # Düz yol mesafesi (km)
    avg_speed_kmh: float = 70  # Ortalama hız
    road_quality: float = 1.0  # Yol kalitesi faktörü (1.0 = normal)
    weather_factor: float = 1.0  # Hava durumu faktörü (1.0 = normal)
    # Phase 5A: Grade distribution (% of climb at each band) - Refined
    grade_gentle_pct: float = 0.8  # 0–2.5% grade (motorway/trunk)
    grade_moderate_pct: float = 0.15  # 2.5–5.5% grade (primary roads)
    grade_steep_pct: float = 0.05  # 5.5%+ grade (mountain passes)
    # Phase 5A: Stop-go proxy
    stopgo_cycles_per_100km: float = 5.0
    # Phase 6: Road type distribution
    otoyol_ratio: float = 0.6
    devlet_yolu_ratio: float = 0.3
    sehir_ici_ratio: float = 0.1
    arac_yasi: int = 5  # Araç yaşı (Gravity Recovery hesabı için)


@dataclass
class FuelPrediction:
    """Yakıt tahmin sonucu"""

    total_liters: float
    consumption_l_100km: float
    energy_breakdown: Dict[str, float]
    confidence_range: Tuple[float, float]
    factors_used: Dict[str, float]
    insight: Optional[str] = None


class PhysicsBasedFuelPredictor:
    """
    Fizik tabanlı yakıt tüketim tahmini.
    """

    # Fiziksel sabitler
    GRAVITY = 9.81  # m/s²
    AIR_DENSITY = 1.225  # kg/m³ (deniz seviyesi)
    MAX_REALISTIC_L_100KM = 65.0
    MIN_REALISTIC_L_100KM = 15.0

    def __init__(self, vehicle: VehicleSpecs = None):
        self.vehicle = vehicle if vehicle else VehicleSpecs()

    @staticmethod
    def _get_gravity_recovery(arac_yasi: int) -> float:
        """Araç yaşına göre dinamik Gravity Recovery faktörü."""
        if arac_yasi <= 3:
            return 0.90
        elif arac_yasi <= 6:
            return 0.80
        elif arac_yasi <= 10:
            return 0.68
        return 0.60

    def predict(
        self, route: RouteConditions, historical_stats: Optional[Dict] = None
    ) -> FuelPrediction:
        """Simple prediction with legacy summary mode"""
        p2p_sim = [
            (route.distance_km * 0.6 * 1000, route.avg_speed_kmh / 3.6, 0.0),
            (
                route.distance_km * 0.2 * 1000,
                route.avg_speed_kmh * 0.8 / 3.6,
                route.ascent_m,
            ),
            (
                route.distance_km * 0.2 * 1000,
                route.avg_speed_kmh / 3.6,
                -route.descent_m,
            ),
        ]
        return self.predict_granular(
            p2p_sim,
            route.load_ton,
            route.is_empty_trip,
            historical_stats=historical_stats,
            arac_yasi=route.arac_yasi,
        )

    def predict_granular(
        self,
        segments: List[Tuple[float, float, float]],
        load_ton: float,
        is_empty_trip: bool = False,
        historical_stats: Optional[Dict] = None,
        **kwargs,
    ) -> FuelPrediction:
        """
        Calculate fuel consumption using point-to-point energy integration.
        segments: List of (distance_m, velocity_ms, elevation_diff_m)
        """
        effective_load = 0.0 if is_empty_trip else load_ton
        total_mass = (
            self.vehicle.empty_weight_kg
            + self.vehicle.trailer_empty_weight_kg
            + (effective_load * 1000)
        )
        arac_yasi = kwargs.get("arac_yasi", 5)

        e_rolling_total = 0.0
        e_air_total = 0.0
        e_climb_total = 0.0
        e_descent_total = 0.0
        total_dist_km = 0.0

        for dist_m, v_ms, delta_h in segments:
            if dist_m <= 0:
                continue

            # Deadband for precision noise
            deadband = 0.3 if v_ms < 15 else (1.0 if v_ms > 22 else 0.5)
            h_eff = delta_h if abs(delta_h) >= deadband else 0.0

            total_dist_km += dist_m / 1000.0

            # 1. Rolling Resistance (Split Tractor/Trailer)
            tractor_mass = self.vehicle.empty_weight_kg
            trailer_and_load_mass = self.vehicle.trailer_empty_weight_kg + (
                effective_load * 1000
            )

            f_roll_tractor = (
                tractor_mass * self.GRAVITY * self.vehicle.rolling_resistance
            )
            f_roll_trailer = (
                trailer_and_load_mass
                * self.GRAVITY
                * self.vehicle.trailer_rolling_resistance
            )
            f_roll = f_roll_tractor + f_roll_trailer
            e_rolling_total += f_roll * dist_m

            # 2. Air Drag (Combined Cd)
            combined_cd = (
                self.vehicle.drag_coefficient + self.vehicle.trailer_drag_contribution
            )
            f_air = (
                0.5
                * self.AIR_DENSITY
                * combined_cd
                * self.vehicle.frontal_area_m2
                * (v_ms**2)
            )
            e_air_total += f_air * dist_m

            # 3. Grade resistance
            f_grade = total_mass * self.GRAVITY * (h_eff / dist_m if dist_m > 0 else 0)
            if f_grade > 0:
                e_climb_total += f_grade * dist_m * 1.05
            else:
                recovery_efficiency = self._get_gravity_recovery(arac_yasi)
                e_descent_total += abs(f_grade) * dist_m * recovery_efficiency

        total_energy_mj = (
            e_rolling_total + e_air_total + e_climb_total - e_descent_total
        ) / 1e6
        total_energy_mj = max(0.1, total_energy_mj)

        fuel_energy_needed_mj = total_energy_mj / self.vehicle.engine_efficiency
        fuel_mass_kg = fuel_energy_needed_mj / self.vehicle.fuel_energy_mj_kg
        fuel_liters = fuel_mass_kg / self.vehicle.fuel_density_kg_l

        if not np.isfinite(fuel_liters):
            fuel_liters = 0.0
        consumption_l_100km = (
            (fuel_liters / total_dist_km * 100) if total_dist_km > 0 else 0.0
        )

        # Clamp logic
        if consumption_l_100km > self.MAX_REALISTIC_L_100KM:
            consumption_l_100km = self.MAX_REALISTIC_L_100KM
            fuel_liters = (consumption_l_100km * total_dist_km) / 100

        # Dynamic Insights
        total_raw = e_rolling_total + e_air_total + e_climb_total
        safe_total = max(1.0, total_raw)
        climb_ratio = e_climb_total / safe_total
        drag_ratio = e_air_total / safe_total

        insight = None
        cl_thr = (
            historical_stats["climb_mean"] + 2 * historical_stats.get("climb_std", 0.1)
            if (historical_stats and "climb_mean" in historical_stats)
            else 0.4
        )
        if climb_ratio > cl_thr:
            diff = int((climb_ratio - cl_thr) * 100)
            insight = f"Dik rampalar tüketimi beklentinin %{diff} üzerinde artırdı"

        dr_thr = (
            historical_stats["drag_mean"] + 2 * historical_stats.get("drag_std", 0.05)
            if (historical_stats and "drag_mean" in historical_stats)
            else 0.6
        )
        if not insight and drag_ratio > dr_thr:
            insight = "Yüksek hız/rüzgar direnci tüketim limitlerini zorladı"

        if not insight and e_descent_total > e_climb_total * 0.8:
            insight = "Sürekli iniş; gravity recovery ile maksimum tasarruf"

        return FuelPrediction(
            total_liters=round(fuel_liters, 2),
            consumption_l_100km=round(consumption_l_100km, 2),
            energy_breakdown={
                "yuvarlanma": round(e_rolling_total / safe_total * 100, 1),
                "hava_direnci": round(e_air_total / safe_total * 100, 1),
                "tirmanis": round(e_climb_total / safe_total * 100, 1),
                "ini_yardimi": round(e_descent_total / safe_total * 100, 1),
            },
            insight=insight,
            confidence_range=(
                round(fuel_liters * 0.92, 1),
                round(fuel_liters * 1.08, 1),
            ),
            factors_used={
                "total_mass_kg": total_mass,
                "distance_km": round(total_dist_km, 2),
                "dynamic_thresholds": historical_stats is not None,
            },
        )

    def calibrate_with_historical(self, predictions: list, actuals: list) -> Dict:
        """Geçmiş verilerle modeli kalibre et."""
        if len(predictions) < 5:
            return {"error": "Minimum 5 veri noktası gerekli"}
        error_ratios = np.array(actuals) / np.maximum(
            np.abs(np.array(predictions)), 1e-6
        )
        return {
            "calibration_factor": round(np.mean(error_ratios), 4),
            "std_deviation": round(np.std(error_ratios), 4),
            "sample_count": len(predictions),
            "recommendation": "Motor verimliliğini güncelle"
            if abs(np.mean(error_ratios) - 1.0) > 0.1
            else "Model kalibre",
        }


class HybridFuelPredictor:
    """Hibrit yaklaşım: Fizik + ML kombinasyonu"""

    def __init__(self, vehicle: VehicleSpecs = None):
        self.physics_model = PhysicsBasedFuelPredictor(vehicle)
        self.correction_factor = 1.0
        self.historical_errors = []

    def predict(self, route: RouteConditions) -> FuelPrediction:
        base = self.physics_model.predict(route)
        corrected_liters = base.total_liters * self.correction_factor
        corrected_cons = (
            (corrected_liters / route.distance_km * 100)
            if route.distance_km > 0
            else 0.0
        )
        margin = corrected_liters * 0.08
        return FuelPrediction(
            total_liters=round(corrected_liters, 1),
            consumption_l_100km=round(corrected_cons, 1),
            energy_breakdown=base.energy_breakdown,
            insight=base.insight,
            confidence_range=(
                round(corrected_liters - margin, 1),
                round(corrected_liters + margin, 1),
            ),
            factors_used={
                **base.factors_used,
                "correction_factor": self.correction_factor,
            },
        )

    def learn_from_actual(self, prediction: float, actual: float):
        """Gerçek değerden öğren (Outlier Guard: ±50%)."""
        ratio = actual / max(abs(prediction), 1e-6)
        if 0.5 < ratio < 1.5:
            self.historical_errors.append(ratio)
        if len(self.historical_errors) >= 5:
            if len(self.historical_errors) > 20:
                self.historical_errors = self.historical_errors[-20:]
            self.correction_factor = float(np.mean(self.historical_errors))
