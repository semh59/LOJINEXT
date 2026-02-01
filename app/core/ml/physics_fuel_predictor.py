"""
TIR Yakıt Takip - Gelişmiş Fizik Tabanlı Yakıt Tahmin Motoru
Enerji formülleri + ML hibrit yaklaşım
"""

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass
class VehicleSpecs:
    """Araç teknik özellikleri"""
    empty_weight_kg: float = 8000      # Boş ağırlık (kg)
    drag_coefficient: float = 0.7      # Hava direnci katsayısı (Cd)
    frontal_area_m2: float = 8.5       # Ön kesit alanı (m²)
    rolling_resistance: float = 0.007  # Yuvarlanma direnci katsayısı
    engine_efficiency: float = 0.38    # Motor verimliliği
    fuel_density_kg_l: float = 0.832   # Dizel yoğunluğu (kg/L)
    fuel_energy_mj_kg: float = 45.5    # Dizel enerji yoğunluğu (MJ/kg)

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
    ascent_m: float = 0         # Toplam tırmanış (metre)
    descent_m: float = 0        # Toplam iniş (metre)
    avg_speed_kmh: float = 70   # Ortalama hız
    road_quality: float = 1.0   # Yol kalitesi faktörü (1.0 = normal)
    weather_factor: float = 1.0 # Hava durumu faktörü (1.0 = normal)


@dataclass
class FuelPrediction:
    """Yakıt tahmin sonucu"""
    total_liters: float
    consumption_l_100km: float
    energy_breakdown: Dict[str, float]
    confidence_range: Tuple[float, float]
    factors_used: Dict[str, float]


class PhysicsBasedFuelPredictor:
    """
    Fizik tabanlı yakıt tüketim tahmini.
    
    Enerji Bileşenleri:
    1. E_rolling = μ × m × g × d (Yuvarlanma direnci)
    2. E_air = 0.5 × ρ × Cd × A × v² × d (Hava direnci)
    3. E_climb = m × g × Δh (Tırmanış enerjisi)
    4. E_accel = Tahmini hızlanma/yavaşlama kayıpları
    """

    # Fiziksel sabitler
    GRAVITY = 9.81  # m/s²
    AIR_DENSITY = 1.225  # kg/m³ (deniz seviyesi)

    def __init__(self, vehicle: VehicleSpecs = None):
        self.vehicle = vehicle or VehicleSpecs()

    def predict(self, route: RouteConditions) -> FuelPrediction:
        """
        Rota koşullarına göre yakıt tahmini yap.
        
        Args:
            route: Rota koşulları
            
        Returns:
            FuelPrediction: Detaylı tahmin sonucu
        """
        # Toplam kütle (araç + yük)
        total_mass = self.vehicle.empty_weight_kg + (route.load_ton * 1000)

        # Mesafe metre cinsine çevir
        distance_m = route.distance_km * 1000

        # Hız m/s cinsine çevir
        speed_ms = route.avg_speed_kmh / 3.6

        # 1. Yuvarlanma direnci enerjisi (Joule)
        e_rolling = (
            self.vehicle.rolling_resistance *
            total_mass *
            self.GRAVITY *
            distance_m *
            route.road_quality
        )

        # 2. Hava direnci enerjisi
        e_air = (
            0.5 *
            self.AIR_DENSITY *
            self.vehicle.drag_coefficient *
            self.vehicle.frontal_area_m2 *
            (speed_ms ** 2) *
            distance_m
        )

        # 3. Tırmanış enerjisi (net yükseklik değişimi)
        net_elevation = route.ascent_m - route.descent_m
        e_climb = total_mass * self.GRAVITY * net_elevation

        # İnişte enerji geri kazanımı modellemesi
        # e_climb < 0 ise, bu enerji yuvarlanma ve hava direncini yenebilir (yakıt tasarrufu)
        # Ancak mekanik kayıplar ve motor freni nedeniyle sadece bir kısmı (~30%) tasarruf sağlar.
        if e_climb < 0:
            e_climb = e_climb * 0.3  # %30 geri kazanım, %70 kayıp

        # 4. Hızlanma/yavaşlama kayıpları (tahmini %15)
        e_accel = (e_rolling + e_air) * 0.15

        # Toplam mekanik enerji (Joule)
        # KRİTİK DÜZELTME: e_climb artık negatif olabilir ve tüketimi azaltır.
        # Ancak toplam enerji idari/mekanik nedenlerle negatif olamaz.
        total_energy_j = max(e_rolling * 0.1, e_rolling + e_air + e_climb + e_accel)

        # MJ'e çevir
        total_energy_mj = total_energy_j / 1_000_000

        # Motor verimliliğini uygula
        fuel_energy_needed_mj = total_energy_mj / self.vehicle.engine_efficiency

        # Hava durumu faktörü
        fuel_energy_needed_mj *= route.weather_factor

        # Yakıt kütlesi (kg)
        fuel_mass_kg = fuel_energy_needed_mj / self.vehicle.fuel_energy_mj_kg

        # Litre cinsine çevir
        fuel_liters = fuel_mass_kg / self.vehicle.fuel_density_kg_l

        # L/100km hesapla (Güvenli bölme)
        consumption_l_100km = (fuel_liters / route.distance_km * 100) if route.distance_km > 0 else 0.0

        # Güven aralığı (%10 margin)
        margin = fuel_liters * 0.10
        confidence = (fuel_liters - margin, fuel_liters + margin)

        # Enerji dağılımı (yüzde) - Numerik korumalı bölme
        total_components = e_rolling + e_air + max(e_climb, 0) + e_accel
        safe_total = max(1.0, total_components)

        return FuelPrediction(
            total_liters=round(fuel_liters, 1),
            consumption_l_100km=round(consumption_l_100km, 1),
            energy_breakdown={
                "yuvarlanma": round(e_rolling / safe_total * 100, 1),
                "hava_direnci": round(e_air / safe_total * 100, 1),
                "tirmanis": round(max(e_climb, 0) / safe_total * 100, 1),
                "hizlanma": round(e_accel / safe_total * 100, 1),
            },
            confidence_range=(round(confidence[0], 1), round(confidence[1], 1)),
            factors_used={
                "toplam_kutle_kg": total_mass,
                "mesafe_km": route.distance_km,
                "yuk_ton": route.load_ton,
                "net_tirmanis_m": net_elevation,
                "ortalama_hiz_kmh": route.avg_speed_kmh,
            }
        )

    def calibrate_with_historical(
        self,
        predictions: list,
        actuals: list
    ) -> Dict:
        """
        Geçmiş verilerle modeli kalibre et.
        
        Args:
            predictions: Tahmin edilen litre değerleri
            actuals: Gerçek litre değerleri
            
        Returns:
            Kalibrasyon parametreleri
        """
        if len(predictions) < 5:
            return {"error": "Minimum 5 veri noktası gerekli"}

        predictions = np.array(predictions)
        actuals = np.array(actuals)

        # Ortalama hata oranı - safe division with epsilon to prevent div-by-zero
        # np.maximum kullanarak element-wise güvenli bölme
        safe_predictions = np.maximum(np.abs(predictions), 1e-6)
        error_ratios = actuals / safe_predictions
        mean_ratio = np.mean(error_ratios)
        std_ratio = np.std(error_ratios)

        return {
            "calibration_factor": round(mean_ratio, 4),
            "std_deviation": round(std_ratio, 4),
            "sample_count": len(predictions),
            "recommendation": "Motor verimlilik değerini güncelle" if abs(mean_ratio - 1.0) > 0.1 else "Model kalibre"
        }


class HybridFuelPredictor:
    """
    Hibrit yaklaşım: Fizik + ML kombinasyonu
    
    1. Fizik modeli baz tahmin yapar
    2. ML model (önceki hatalardan öğrenir) düzeltme faktörü uygular
    """

    def __init__(self, vehicle: VehicleSpecs = None):
        self.physics_model = PhysicsBasedFuelPredictor(vehicle)
        self.correction_factor = 1.0
        self.historical_errors = []

    def predict(self, route: RouteConditions) -> FuelPrediction:
        """Hibrit tahmin"""
        # Fizik tabanlı tahmin
        base_prediction = self.physics_model.predict(route)

        # ML düzeltme faktörü uygula
        corrected_liters = base_prediction.total_liters * self.correction_factor
        corrected_consumption = (corrected_liters / route.distance_km) * 100 if route.distance_km > 0 else 0.0

        margin = corrected_liters * 0.08  # %8 margin (daha dar)

        return FuelPrediction(
            total_liters=round(corrected_liters, 1),
            consumption_l_100km=round(corrected_consumption, 1),
            energy_breakdown=base_prediction.energy_breakdown,
            confidence_range=(
                round(corrected_liters - margin, 1),
                round(corrected_liters + margin, 1)
            ),
            factors_used={
                **base_prediction.factors_used,
                "correction_factor": self.correction_factor
            }
        )

    def learn_from_actual(self, prediction: float, actual: float):
        """Gerçek değerden öğren"""
        # Güvenli bölme: prediction sıfır veya çok küçük ise epsilon kullan
        safe_prediction = max(abs(prediction), 1e-6)
        error_ratio = actual / safe_prediction
        self.historical_errors.append(error_ratio)

        # Son 20 hatanın ortalaması ile güncelle
        if len(self.historical_errors) > 20:
            self.historical_errors = self.historical_errors[-20:]

        self.correction_factor = np.mean(self.historical_errors)
