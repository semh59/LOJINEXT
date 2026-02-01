"""
TIR Yakıt Takip Sistemi - Analiz Servisi
Gelişmiş algoritmalar: Periyot oluşturma, yakıt dağıtımı, anomali tespiti
Async Refactoring: Ağır hesaplamalar ve I/O işlemleri thread pool'da çalıştırılır.
PostgreSQL Migration: SQLite kaldırıldı, PostgreSQL kullanılıyor.
"""

import asyncio
import threading
from dataclasses import dataclass
from datetime import date
from itertools import groupby
from statistics import mean, stdev
from typing import Dict, List, Optional, TypedDict

from app.core.entities import (
    AnomalyResult,
    Sefer,
    SeverityEnum,
    VehicleStats,
    YakitAlimi,
    YakitPeriyodu,
)
from app.config import settings
from app.infrastructure.cache.cache_manager import get_cache_manager


@dataclass
class PeriyotSeferMatch:
    """Periyot-sefer eşleştirme sonucu"""

    periyot: YakitPeriyodu
    seferler: List[Sefer]
    toplam_mesafe: int
    dagitim_yapildi: bool


class TrendResult(TypedDict):
    slope: float
    direction: str
    strength: float


class RegressionResult(TypedDict):
    ortalama: float
    guvenilirlik: float
    toplam_km: int
    toplam_yakit: float


class AnalizService:
    """
    Gelişmiş analiz servisi (Async).

    Tüm ağır hesaplamalar (O(N Log N) vb.) ve Veritabanı I/O işlemleri
    Async Wrapper pattern ile Thread Pool'a (`asyncio.to_thread`) yönlendirilir.
    """

    def __init__(self, yakit_repo=None, sefer_repo=None, arac_repo=None):
        """
        Analiz servisi - Repo pattern ile çalışır.
        """
        # DI
        if yakit_repo:
            self.yakit_repo = yakit_repo
        else:
            from app.database.repositories.yakit_repo import get_yakit_repo

            self.yakit_repo = get_yakit_repo()

        if sefer_repo:
            self.sefer_repo = sefer_repo
        else:
            from app.database.repositories.sefer_repo import get_sefer_repo

            self.sefer_repo = get_sefer_repo()

        # Arac Repo - currently unused but kept for Container consistency
        self.arac_repo = arac_repo

        self.cache = get_cache_manager()
        # self._cache_stats and self._cache_regression are now handled by self.cache

    # ============== YAKIT PERİYOT OLUŞTURMA (ASYNC) ==============

    async def create_fuel_periods(self, fuel_records: List[YakitAlimi]) -> List[YakitPeriyodu]:
        """İki yakıt alımı arası periyotları oluştur (Async)"""
        return await asyncio.to_thread(self._sync_create_fuel_periods, fuel_records)

    def _sync_create_fuel_periods(self, fuel_records: List[YakitAlimi]) -> List[YakitPeriyodu]:
        """
        İki yakıt alımı arası periyotları oluştur.
        Algoritma: O(n log n)
        """
        if len(fuel_records) < 2:
            return []

        # Database defines the order now (ASC)
        sorted_records = fuel_records

        # Araç bazlı grupla
        periods = []

        for arac_id, group in groupby(sorted_records, key=lambda x: x.arac_id):
            records = list(group)

            # Ardışık çiftler oluştur
            for i in range(len(records) - 1):
                r1, r2 = records[i], records[i + 1]

                # Mesafe hesapla
                distance = r2.km_sayac - r1.km_sayac

                # Negatif veya sıfır mesafe = veri hatası, atla
                if distance <= 0:
                    continue

                # Tüketim hesapla (L/100km)
                # İkinci alımdaki yakıt = bu periyotta kullanılan
                consumption = (r2.litre / distance) * 100 if distance > 0 else 0

                period = YakitPeriyodu(
                    arac_id=arac_id,
                    alim1_id=r1.id,
                    alim2_id=r2.id,
                    alim1_tarih=r1.tarih,
                    alim1_km=r1.km_sayac,
                    alim1_litre=r1.litre,
                    alim2_tarih=r2.tarih,
                    alim2_km=r2.km_sayac,
                    ara_mesafe=distance,
                    toplam_yakit=r2.litre,
                    ort_tuketim=round(consumption, 2),
                    durum=self._evaluate_consumption_status(consumption),
                )
                periods.append(period)

        return periods

    def _evaluate_consumption_status(self, consumption: float) -> str:
        """Tüketim durumunu değerlendir"""
        if consumption < 20:
            return "ÇOK DÜŞÜK - Veri hatası?"
        elif consumption < 28:
            return "MÜKEMMEL"
        elif consumption < 32:
            return "İYİ"
        elif consumption < 38:
            return "NORMAL"
        elif consumption < 45:
            return "YÜKSEK"
        else:
            return "ANORMALİ - Kontrol gerekli"

    # ============== AĞIRLIKLI YAKIT DAĞITIMI (ASYNC) ==============

    async def distribute_fuel_to_trips(
        self, period: YakitPeriyodu, trips: List[Sefer]
    ) -> List[Sefer]:
        """Periyottaki yakıtı seferlere Ton-Km oranında dağıt (Async)"""
        return await asyncio.to_thread(self._sync_distribute_fuel_to_trips, period, trips)

    def _sync_distribute_fuel_to_trips(
        self, period: YakitPeriyodu, trips: List[Sefer]
    ) -> List[Sefer]:
        """
        Periyottaki yakıtı seferlere Ton-Km (Tonaj * Mesafe) oranında dağıt.
        """
        if not trips:
            return trips

        # Config-driven sabitler
        empty_weight = settings.HGV_EMPTY_WEIGHT  # Ortalama TIR boş ağırlığı

        # 1. Her seferin faktörünü hesapla
        trip_factors = []
        total_factor = 0.0

        for trip in trips:
            # Tonaj (Veri yoksa 0 kabul et)
            load_ton = (trip.net_kg or 0) / 1000.0 if trip.net_kg else (trip.ton or 0.0)

            # Toplam kütle
            total_mass = empty_weight + load_ton

            # Faktör: Mesafe * Kütle (Ton-Km prensibi)
            # Mesafe yoksa faktör 0
            factor = trip.mesafe_km * total_mass if trip.mesafe_km > 0 else 0

            trip_factors.append(factor)
            total_factor += factor

        if total_factor <= 0:
            # Mesafe veya veri hatası varsa, eşit/mesafe bazlı dağıtıma fallback yap
            # Fallback: Sadece mesafeye göre
            total_distance = sum(t.mesafe_km for t in trips)
            if total_distance == 0:
                return trips

            # Basit mesafe bazlı dağıtım (Fallback)
            remaining_fuel = period.toplam_yakit
            for i, trip in enumerate(trips):
                weight = trip.mesafe_km / total_distance
                if i < len(trips) - 1:
                    fuel = round(period.toplam_yakit * weight, 2)
                    remaining_fuel -= fuel
                else:
                    fuel = round(remaining_fuel, 2)

                trip.dagitilan_yakit = fuel
                trip.tuketim = round((fuel / trip.mesafe_km * 100), 2) if trip.mesafe_km else 0
                trip.periyot_id = period.id
            return trips

        # 2. Ton-Km bazlı dağıtım
        remaining_fuel = period.toplam_yakit

        for i, trip in enumerate(trips):
            factor = trip_factors[i]

            # Oran
            ratio = factor / total_factor

            if i < len(trips) - 1:
                fuel_allocated = round(period.toplam_yakit * ratio, 2)
                remaining_fuel -= fuel_allocated
            else:
                fuel_allocated = round(remaining_fuel, 2)

            # Tüketim (L/100km)
            consumption = 0.0
            if trip.mesafe_km > 0:
                consumption = round((fuel_allocated / trip.mesafe_km) * 100, 2)

            # Sefer objesini güncelle
            trip.dagitilan_yakit = fuel_allocated
            trip.tuketim = consumption
            trip.periyot_id = period.id

        return trips

    async def match_periods_with_trips(
        self, periods: List[YakitPeriyodu], all_trips: List[Sefer]
    ) -> List[PeriyotSeferMatch]:
        """Periyotları ilgili seferlerle eşleştir (Async)"""
        return await asyncio.to_thread(self._sync_match_periods_with_trips, periods, all_trips)

    def _sync_match_periods_with_trips(
        self, periods: List[YakitPeriyodu], all_trips: List[Sefer]
    ) -> List[PeriyotSeferMatch]:
        """
        Periyotları ilgili seferlerle eşleştir.
        """
        matches = []

        # Seferleri araç ve tarihe göre indeksle (O(n))
        trip_index: Dict[int, List[Sefer]] = {}
        for trip in all_trips:
            if trip.arac_id not in trip_index:
                trip_index[trip.arac_id] = []
            trip_index[trip.arac_id].append(trip)

        # Her periyot için eşleştir
        for period in periods:
            matching_trips = []

            # Bu aracın seferlerini al
            vehicle_trips = trip_index.get(period.arac_id, [])

            # Periyot tarih aralığındaki seferleri bul
            for trip in vehicle_trips:
                if period.alim1_tarih <= trip.tarih < period.alim2_tarih:
                    matching_trips.append(trip)

            # Tarihe göre sıralama artık DB tarafında yapılıyor (desc=False)
            # matching_trips.sort(key=lambda x: (x.tarih, x.saat or ""))

            # Yakıt dağıt
            if matching_trips:
                # self.distribute normalde asenkron wrapper, ama burada sync içinden çağırıyoruz.
                # Direkt _sync versiyonunu çağırmalıyız.
                matching_trips = self._sync_distribute_fuel_to_trips(period, matching_trips)

            matches.append(
                PeriyotSeferMatch(
                    periyot=period,
                    seferler=matching_trips,
                    toplam_mesafe=sum(t.mesafe_km for t in matching_trips),
                    dagitim_yapildi=len(matching_trips) > 0,
                )
            )

        return matches

    # ============== ANOMALİ TESPİTİ (ASYNC) ==============

    async def detect_anomalies(
        self, consumptions: List[float], z_threshold: float = 2.5, use_iqr: bool = True
    ) -> List[AnomalyResult]:
        """Z-Score ve IQR ile anomali tespiti (Async)"""
        return await asyncio.to_thread(
            self._sync_detect_anomalies, consumptions, z_threshold, use_iqr
        )

    def _sync_detect_anomalies(
        self, consumptions: List[float], z_threshold: float = 2.5, use_iqr: bool = True
    ) -> List[AnomalyResult]:
        """
        Z-Score ve IQR ile anomali tespiti.
        """
        if len(consumptions) < 5:
            return []  # Yeterli veri yok

        # Temel istatistikler
        avg = mean(consumptions)
        std = stdev(consumptions) if len(consumptions) > 1 else 1

        # Z-Score hesapla
        z_scores = [(c - avg) / std if std > 0 else 0 for c in consumptions]

        # IQR hesapla
        sorted_c = sorted(consumptions)
        n = len(sorted_c)
        q1 = sorted_c[n // 4]
        q3 = sorted_c[3 * n // 4]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        anomalies = []

        for i, c in enumerate(consumptions):
            z = z_scores[i]
            is_z_anomaly = abs(z) > z_threshold
            is_iqr_anomaly = c < lower_bound or c > upper_bound

            # Şiddet belirleme
            severity = None
            message = ""

            if use_iqr:
                # Her iki yöntemle de anomali = HIGH
                if is_z_anomaly and is_iqr_anomaly:
                    if abs(z) > 3.5:
                        severity = SeverityEnum.CRITICAL
                        message = f"Kritik anomali: {c:.1f} L/100km (Z={z:.2f})"
                    else:
                        severity = SeverityEnum.HIGH
                        message = f"Yüksek anomali: {c:.1f} L/100km (Z={z:.2f})"
                # Sadece bir yöntemle anomali = MEDIUM
                elif is_z_anomaly or is_iqr_anomaly:
                    severity = SeverityEnum.MEDIUM
                    message = f"Orta anomali: {c:.1f} L/100km"
            else:
                # Sadece Z-Score kullan
                if is_z_anomaly:
                    if abs(z) > 3.5:
                        severity = SeverityEnum.CRITICAL
                    elif abs(z) > 3.0:
                        severity = SeverityEnum.HIGH
                    else:
                        severity = SeverityEnum.MEDIUM
                    message = f"Anomali: {c:.1f} L/100km (Z={z:.2f})"

            if severity:
                anomalies.append(
                    AnomalyResult(index=i, value=c, z_score=z, severity=severity, message=message)
                )

        return anomalies

    async def analyze_vehicle_consumption(
        self, arac_id: int, consumptions: List[float]
    ) -> VehicleStats:
        """Araç tüketim analizi (Async)"""
        cache_key = f"stats_{arac_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        result = await asyncio.to_thread(
            self._sync_analyze_vehicle_consumption, arac_id, consumptions
        )

        self.cache.set(cache_key, result, ttl_seconds=3600)
        return result

    def _sync_analyze_vehicle_consumption(
        self, arac_id: int, consumptions: List[float]
    ) -> VehicleStats:
        """Araç tüketim analizi (Sync)"""
        # _sync versiyonunu çağırdığımızdan, burada da _sync versiyonunu kullanmalıyız.
        # detect_anomalies CPU bound ama ağır değil. Yine de _sync çağıralım.
        anomalies = self._sync_detect_anomalies(consumptions)

        # Anomalisiz ortala (outlier removal)
        anomaly_indices = {
            a.index for a in anomalies if a.severity in [SeverityEnum.HIGH, SeverityEnum.CRITICAL]
        }
        clean_consumptions = [c for i, c in enumerate(consumptions) if i not in anomaly_indices]

        avg_consumption = (
            mean(clean_consumptions)
            if clean_consumptions
            else mean(consumptions)
            if consumptions
            else 0
        )

        return VehicleStats(
            arac_id=arac_id,
            plaka="",  # Caller tarafından doldurulacak
            ort_tuketim=round(avg_consumption, 2),
            en_iyi_tuketim=min(consumptions) if consumptions else None,
            en_kotu_tuketim=max(consumptions) if consumptions else None,
            anomali_sayisi=len(anomalies),
        )

    # ============== İSTATİSTİKLER (Cached) ==============

    async def get_fleet_average(self, year: int, month: int) -> float:
        """Filo ortalaması (cached)."""
        cache_key = f"fleet_avg_{year}_{month}"
        cached_val = self.cache.get(cache_key)
        if cached_val is not None:
            return cached_val

        # Gerçek implementasyon analiz_repo'dan gelmeli
        from app.database.repositories.analiz_repo import get_analiz_repo

        repo = get_analiz_repo()
        val = await repo.get_filo_ortalama_tuketim()

        self.cache.set(cache_key, val, ttl_seconds=3600)  # 1 saat
        return val

    def calculate_moving_average(
        self, values: List[float], window: int = 5
    ) -> List[Optional[float]]:
        """Hareketli ortalama hesapla."""
        result = []
        for i in range(len(values)):
            if i < window - 1:
                result.append(None)
            else:
                window_values = values[i - window + 1 : i + 1]
                result.append(round(mean(window_values), 2))
        return result

    def calculate_trend(self, values: List[float]) -> TrendResult:
        """Trend analizi (basit lineer regresyon)."""
        if len(values) < 3:
            return {"slope": 0, "direction": "stable", "strength": 0}

        n = len(values)
        x = list(range(n))

        # Lineer regresyon
        x_mean = mean(x)
        y_mean = mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0

        # Trend yönü ve gücü
        if abs(slope) < 0.1:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        # R-squared (basit)
        ss_tot = sum((v - y_mean) ** 2 for v in values)
        y_pred = [y_mean + slope * (i - x_mean) for i in x]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {"slope": round(slope, 4), "direction": direction, "strength": round(r_squared, 4)}

    async def calculate_long_term_stats(self, arac_id: int) -> Optional[RegressionResult]:
        """
        Uzun dönem regresyon analizi (Async).
        """
        # Check cache via CacheManager
        cache_key = f"regression_{arac_id}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        alimlar = await self.yakit_repo.get_all(arac_id=arac_id, limit=1000, desc=False)
        if len(alimlar) < 3:
            return None

        # Sıralama artık DB tarafında yapılıyor (desc=False)
        # alimlar.sort(key=lambda x: x["km_sayac"])

        # Veri setini oluştur
        x_data = []  # Kümülatif KM
        y_data = []  # Kümülatif Yakıt

        cum_liter = 0
        start_km = alimlar[0]["km_sayac"]

        for a in alimlar:
            cum_liter += a["litre"]
            current_distance = a["km_sayac"] - start_km

            if current_distance > 0:
                x_data.append(current_distance)
                y_data.append(cum_liter)

        if len(x_data) < 3:
            return None

        # Lineer Regresyon (Least Squares)
        n = len(x_data)
        x_mean = sum(x_data) / n
        y_mean = sum(y_data) / n

        numerator = sum((x_data[i] - x_mean) * (y_data[i] - y_mean) for i in range(n))
        denominator = sum((x_data[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return None

        slope = numerator / denominator
        consumption_per_100 = slope * 100

        # R-Square (Güvenilirlik)
        ss_tot = sum((y - y_mean) ** 2 for y in y_data)
        y_pred = [y_mean + slope * (x - x_mean) for x in x_data]
        ss_res = sum((y_data[i] - y_pred[i]) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        result = {
            "ortalama": round(consumption_per_100, 2),
            "guvenilirlik": round(r_squared * 100, 1),  # %
            "toplam_km": x_data[-1],
            "toplam_yakit": cum_liter,
        }

        # Cache result
        self.cache.set(cache_key, result, ttl_seconds=86400)  # 24 saat
        return result

    def clear_cache(self):
        """Tüm cache'i temizle"""
        self.cache.clear()

    async def recalculate_vehicle_periods(self, arac_id: int):
        """
        Bir aracın tüm yakıt periyotlarını yeniden hesapla, seferlerle eşleştir ve kaydet (Async).
        """
        # 1. Tüm veri setini getir (Yakıtlar ve Seferler)
        fuel_records = []
        raw_alimlar = await self.yakit_repo.get_all(arac_id=arac_id, limit=2000, desc=False)
        for r in raw_alimlar:
            fuel_records.append(
                YakitAlimi(
                    id=r["id"],
                    tarih=date.fromisoformat(r["tarih"])
                    if isinstance(r["tarih"], str)
                    else r["tarih"],
                    arac_id=r["arac_id"],
                    istasyon=r["istasyon"],
                    fiyat_tl=round(float(r["fiyat_tl"]), 2),
                    litre=float(r["litre"]),
                    km_sayac=int(r["km_sayac"]),
                    fis_no=r["fis_no"],
                )
            )

        all_trips = []
        raw_seferler = await self.sefer_repo.get_all(arac_id=arac_id, limit=5000, desc=False)
        for s in raw_seferler:
            all_trips.append(
                Sefer(
                    id=s["id"],
                    tarih=date.fromisoformat(s["tarih"])
                    if isinstance(s["tarih"], str)
                    else s["tarih"],
                    arac_id=s["arac_id"],
                    sofor_id=s["sofor_id"],
                    cikis_yeri=s["cikis_yeri"],
                    varis_yeri=s["varis_yeri"],
                    mesafe_km=int(s["mesafe_km"]),
                    # ton computed_field, constructor'da verilmez - otomatik hesaplanır
                    net_kg=int(s["net_kg"]),
                    durum=s["durum"],
                )
            )

        # 2. Periyotları hesapla (sync çağrısı çünkü içerde async gerekmez, CPU bound)
        # Note: _sync_create_fuel_periods is pure CPU logic.
        periods = self._sync_create_fuel_periods(fuel_records)

        # 3. Periyotları kaydet (ID almak için gerekli)
        if periods:
            await self.yakit_repo.save_fuel_periods(periods, clear_existing=True)
            # Kaydedilen periyotları ID'leri ile geri okumak ideal olurdu ama
            # şimdilik tekrar çekelim veya match_periods logic'i ID olmadan çalışıyor mu bakalım.
            # match_periods periyot.id kullanıyor mu? Evet, trip.periyot_id ataması için.
            # Bu yüzden tekrar çekmemiz lazım.

            saved_period_dicts = await self.yakit_repo.get_fuel_periods(arac_id, limit=1000)
            # Dict -> Entity
            saved_periods = []
            for p in saved_period_dicts:
                saved_periods.append(
                    YakitPeriyodu(
                        id=p["id"],
                        arac_id=p["arac_id"],
                        alim1_id=p["alim1_id"],
                        alim2_id=p["alim2_id"],
                        alim1_tarih=date.fromisoformat(p["alim1_tarih"])
                        if isinstance(p["alim1_tarih"], str)
                        else p["alim1_tarih"],
                        alim1_km=p["alim1_km"],
                        alim1_litre=p["alim1_litre"],
                        alim2_tarih=date.fromisoformat(p["alim2_tarih"])
                        if isinstance(p["alim2_tarih"], str)
                        else p["alim2_tarih"],
                        alim2_km=p["alim2_km"],
                        ara_mesafe=p["ara_mesafe"],
                        toplam_yakit=p["toplam_yakit"],
                        ort_tuketim=p["ort_tuketim"],
                        durum=p["durum"],
                    )
                )

            # 4. Seferlerle eşleştir ve yakıtı dağıt
            matches = self._sync_match_periods_with_trips(saved_periods, all_trips)

            # 5. Güncellenen seferleri kaydet
            updated_trips = []
            for m in matches:
                updated_trips.extend(m.seferler)

            if updated_trips:
                await self.sefer_repo.update_trips_fuel_data(updated_trips)

        # 6. Cache temizle
        self.cache.delete(f"stats_{arac_id}")
        self.cache.delete(f"regression_{arac_id}")


# Thread-safe Singleton Instance
_analiz_service: Optional[AnalizService] = None
_analiz_service_lock = threading.Lock()


def get_analiz_service() -> AnalizService:
    """Thread-safe Singleton AnalizService provider"""
    global _analiz_service
    if _analiz_service is None:
        with _analiz_service_lock:
            if _analiz_service is None:
                _analiz_service = AnalizService()
    return _analiz_service
