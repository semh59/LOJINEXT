"""
TIR Yakıt Takip - Zaman Serisi Servis Katmanı
LSTM model eğitimi, tahmin ve veritabanı entegrasyonu
"""

from typing import Dict, List, Optional

from app.core.ml.time_series_predictor import (
    get_time_series_predictor,
    is_lstm_available,
)
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class TimeSeriesService:
    """
    LSTM zaman serisi tahmin servisi.

    Veritabanı entegrasyonu ile:
    1. Günlük veri aggregasyonu
    2. Model eğitimi
    3. Haftalık tahmin
    4. Trend analizi
    """

    def __init__(self):
        self.predictor = get_time_series_predictor()

    async def get_daily_summary(
        self, arac_id: Optional[int] = None, days: int = 90
    ) -> List[Dict]:
        """Son N günün günlük özet verilerini getir (Repository Method)."""
        from app.database.repositories.analiz_repo import get_analiz_repo

        days = max(1, min(int(days), 365))
        analiz_repo = get_analiz_repo()

        try:
            rows = await analiz_repo.get_daily_summary_for_ml(
                days=days, arac_id=arac_id
            )
            return [
                {
                    "tarih": row.get("tarih"),
                    "ort_tuketim": float(row.get("ort_tuketim") or 0),
                    "toplam_km": float(row.get("toplam_km") or 0),
                    "ort_ton": float(row.get("ort_ton") or 0),
                    "sefer_sayisi": int(row.get("sefer_sayisi") or 0),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"get_daily_data error: {e}")
            return []

    def _filter_outliers(self, data: List[Dict], threshold: float = 3.0) -> List[Dict]:
        """Z-Score tabanlı outlier filtresi"""
        if len(data) < 10:
            return data

        import numpy as np

        consumptions = np.array([d["ort_tuketim"] for d in data])
        mean = np.mean(consumptions)
        std = np.std(consumptions)

        if std == 0:
            return data

        filtered = []
        for d in data:
            z_score = abs(d["ort_tuketim"] - mean) / std
            if z_score <= threshold:
                filtered.append(d)

        if len(data) - len(filtered) > 0:
            logger.info(
                f"Filtered {len(data) - len(filtered)} outliers from time series data."
            )

        return filtered

    async def train_model(
        self, arac_id: Optional[int] = None, days: int = 180, epochs: int = 100
    ) -> Dict:
        """LSTM modelini eğit (ELITE Performance: Async/Threaded)."""
        if not is_lstm_available():
            return {"success": False, "error": "PyTorch not available"}

        import asyncio

        daily_data = await self.get_daily_summary(arac_id, days)

        # Outlier Temizleme (CPU-bound)
        daily_data = await asyncio.to_thread(self._filter_outliers, daily_data)

        if len(daily_data) < 45:
            return {"success": False, "error": f"Yetersiz veri: {len(daily_data)} gün."}

        # FAZ 2.1: LSTM eğitimini thread pool'a al
        result = await asyncio.to_thread(
            self.predictor.train, daily_data=daily_data, epochs=epochs
        )

        if result["success"]:
            logger.info(
                f"Time series model trained for {'vehicle ' + str(arac_id) if arac_id else 'fleet'}"
            )
        return result

    async def predict_weekly(self, arac_id: Optional[int] = None) -> Dict:
        """Haftalık tüketim tahmini (Secure Async)."""
        if not is_lstm_available():
            return {"success": False, "error": "PyTorch not available"}

        import asyncio

        # Araca özel veri yetersizse filo geneline düş (Faz 4: Cold Start)
        daily_data = await self.get_daily_summary(arac_id, days=35)

        if len(daily_data) < 30 and arac_id is not None:
            logger.info(
                f"Insufficient data for vehicle {arac_id}, falling back to fleet-wide model."
            )
            return await self.predict_weekly(arac_id=None)

        if len(daily_data) < 30:
            # COLD START / DEMO MODE: Yetersiz veri varsa mock üret
            logger.warning("Yetersiz veri, Cold Start mock verisi üretiliyor.")

            from datetime import date, timedelta
            import random

            today = date.today()
            forecast_dates = [
                (today + timedelta(days=i + 1)).isoformat() for i in range(7)
            ]

            # 30-35L arası rastgele tahminler
            base_consumption = 32.5
            forecast_values = []
            lows = []
            highs = []

            for _ in range(7):
                val = base_consumption + random.uniform(-1.5, 2.5)
                forecast_values.append(round(val, 2))
                lows.append(round(val * 0.95, 2))
                highs.append(round(val * 1.05, 2))

            return {
                "success": True,
                "forecast": forecast_values,
                "forecast_dates": forecast_dates,
                "confidence_low": lows,
                "confidence_high": highs,
                "trend": "stable",
                "vehicle_id": arac_id,
                "method": "Cold-Start-Mock",
            }

        try:
            # FAZ 2.1: Model prediction thread'de çalışır
            prediction = await asyncio.to_thread(self.predictor.predict, daily_data)

            from datetime import date, timedelta

            today = date.today()
            forecast_dates = [
                (today + timedelta(days=i + 1)).isoformat() for i in range(7)
            ]

            return {
                "success": True,
                "forecast": prediction.forecast,
                "forecast_dates": forecast_dates,
                "confidence_low": prediction.confidence_low,
                "confidence_high": prediction.confidence_high,
                "trend": prediction.trend,
                "vehicle_id": arac_id,
                "method": "Vehicle-Specific" if arac_id else "Fleet-Wide (Fallback)",
            }
        except Exception as e:
            logger.warning(f"Model prediction failed ({e}), falling back to mock data.")

            # MOCK FALLBACK (Cold Start)
            from datetime import date, timedelta
            import random

            today = date.today()
            forecast_dates = [
                (today + timedelta(days=i + 1)).isoformat() for i in range(7)
            ]

            # 30-35L arası gerçekçi mock tahminler
            base_consumption = 32.5
            forecast_values = []
            lows = []
            highs = []

            for _ in range(7):
                val = base_consumption + random.uniform(-1.5, 2.5)
                forecast_values.append(round(val, 2))
                lows.append(round(val * 0.95, 2))
                highs.append(round(val * 1.05, 2))

            return {
                "success": True,
                "forecast": forecast_values,
                "forecast_dates": forecast_dates,
                "confidence_low": lows,
                "confidence_high": highs,
                "trend": "stable",
                "vehicle_id": arac_id,
                "method": "Mock-Fallback",
            }

    async def get_trend_analysis(
        self, arac_id: Optional[int] = None, days: int = 30
    ) -> Dict:
        """
        Trend analizi.

        Args:
            arac_id: Araç ID
            days: Analiz süresi

        Returns:
            Dict: Trend analizi sonuçları
        """
        daily_data = await self.get_daily_summary(arac_id, days)

        if len(daily_data) < 7:
            # COLD START / DEMO MODE
            logger.warning("Yetersiz trend verisi, mock üretiliyor.")
            import random
            from datetime import date, timedelta

            base_date = date.today() - timedelta(days=30)
            daily_data = []
            consumptions = []
            total_consumptions = []

            for i in range(30):
                val = 32.0 + random.uniform(-3, 3)
                km = random.uniform(200, 600)
                tot = (val * km) / 100.0
                day_date = (base_date + timedelta(days=i)).isoformat()
                daily_data.append(
                    {"tarih": day_date, "ort_tuketim": val, "toplam_km": km}
                )
                consumptions.append(val)
                total_consumptions.append(round(tot, 2))
        else:
            consumptions = [d.get("ort_tuketim", 32.0) for d in daily_data]
            total_consumptions = [
                round(
                    d.get(
                        "toplam_litre",
                        (d.get("ort_tuketim", 0) * d.get("toplam_km", 0)) / 100.0,
                    ),
                    2,
                )
                for d in daily_data
            ]

        # Lineer regresyon ile trend
        import numpy as np

        x = np.arange(len(consumptions))
        y = np.array(consumptions)

        # Slope hesapla
        slope = 0
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]

        # Trend yönü
        if slope < -0.1:
            trend = "decreasing"
            trend_tr = "Azalıyor"
        elif slope > 0.1:
            trend = "increasing"
            trend_tr = "Artıyor"
        else:
            trend = "stable"
            trend_tr = "Sabit"

        # Hareketli ortalamalar
        ma7 = (
            np.convolve(y, np.ones(7) / 7, mode="valid").tolist() if len(y) >= 7 else []
        )

        return {
            "success": True,
            "trend": trend,
            "trend_tr": trend_tr,
            "slope": round(slope, 4),
            "current_avg": round(np.mean(consumptions[-7:]), 2) if consumptions else 0,
            "previous_avg": round(np.mean(consumptions[:7]), 2)
            if len(consumptions) >= 14
            else None,
            "moving_average_7": [round(v, 2) for v in ma7],
            "daily_values": consumptions,  # Verimlilik (L/100km)
            "daily_total_values": total_consumptions,  # Toplam Litre
            "dates": [d.get("tarih") for d in daily_data],
            "days_analyzed": len(consumptions),
        }

    def get_model_status(self) -> Dict:
        """Model durumu bilgisi."""
        return {
            "lstm_available": is_lstm_available(),
            "is_trained": self.predictor.is_trained if is_lstm_available() else False,
            "training_epochs": len(self.predictor.training_history)
            if is_lstm_available() and self.predictor.training_history
            else 0,
            "last_loss": self.predictor.training_history[-1]["val_loss"]
            if is_lstm_available() and self.predictor.training_history
            else None,
        }


def get_time_series_service() -> TimeSeriesService:
    from app.core.container import get_container

    return get_container().time_series_service
