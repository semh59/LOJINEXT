import threading
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional


from app.infrastructure.logging.logger import get_logger
from app.database.unit_of_work import get_uow

logger = get_logger(__name__)


class InsightType(str, Enum):
    """Insight tipleri"""
    UYARI = "uyari"
    IYILESME = "iyilesme"
    ONERI = "oneri"
    TREND = "trend"


@dataclass
class Insight:
    """Otomatik üretilen insight"""
    tip: InsightType
    kaynak_tip: str  # 'arac', 'sofor', 'filo'
    kaynak_id: Optional[int]
    mesaj: str
    onem_puani: int = 50  # 0-100
    tarih: date = None

    def __post_init__(self):
        if self.tarih is None:
            self.tarih = date.today()


class InsightEngine:
    """
    Elite Insight Motoru (Async & Optimized)
    
    Analiz kategorileri:
    - Araç performans (Bulk Intelligence)
    - Şoför performans (Evaluation Service)
    - Filo genel trendler
    """

    def __init__(self):
        pass

    async def generate_vehicle_insights_bulk(self) -> List[Insight]:
        """Tüm araçlar için toplu insight üret (N+1 Fix)"""
        insights = []
        uow = get_uow()
        
        async with uow:
            # 1. Toplu istatistikleri çek (Tek sorgu!)
            stats = await uow.analiz_repo.get_all_vehicles_consumption_stats(days=30)
            
            for s in stats:
                arac_id = s['arac_id']
                plaka = s['plaka']
                hedef = s['hedef_tuketim'] or 32.0
                ortalama = s['ort_tuketim'] or 0.0
                
                if ortalama <= 0: continue
                
                # Hedeften sapma
                sapma = ((ortalama - hedef) / hedef) * 100 if hedef > 0 else 0

                if sapma > 10:
                    insights.append(Insight(
                        tip=InsightType.UYARI,
                        kaynak_tip='arac',
                        kaynak_id=arac_id,
                        mesaj=f"Araç {plaka}: Hedef tüketimin %{sapma:.1f} üzerinde",
                        onem_puani=75 if sapma > 20 else 60
                    ))
                elif sapma < -5:
                    insights.append(Insight(
                        tip=InsightType.IYILESME,
                        kaynak_tip='arac',
                        kaynak_id=arac_id,
                        mesaj=f"Araç {plaka}: Hedefin %{abs(sapma):.1f} altında verimli",
                        onem_puani=60
                    ))

                # Trend analizi (İlk 15 gün vs Son 15 gün)
                son_15 = s.get('son_15_gun_ort')
                onceki_15 = s.get('onceki_15_gun_ort')
                
                if son_15 and onceki_15:
                    trend = ((son_15 - onceki_15) / onceki_15) * 100
                    if abs(trend) > 10:
                        msg = f"Araç {plaka}: Tüketim son 15 günde %{abs(trend):.1f} {'arttı' if trend > 0 else 'azaldı'}"
                        insights.append(Insight(
                            tip=InsightType.TREND if trend > 0 else InsightType.IYILESME,
                            kaynak_tip='arac',
                            kaynak_id=arac_id,
                            mesaj=msg,
                            onem_puani=65
                        ))

        return insights

    async def generate_driver_insights_bulk(self) -> List[Insight]:
        """Tüm şoförler için insight üret"""
        insights = []
        from app.core.container import get_container
        
        deger_service = get_container().degerlendirme_service
        evaluations = await deger_service.get_all_evaluations()
        
        for eval in evaluations:
            sid = eval.sofor_id
            ad = eval.ad_soyad
            puan = eval.genel_puan
            
            if puan >= 90:
                insights.append(Insight(tip=InsightType.IYILESME, kaynak_tip='sofor', kaynak_id=sid, 
                                        mesaj=f"{ad}: Mükemmel performans ({puan}/100)", onem_puani=70))
            elif puan < 50:
                insights.append(Insight(tip=InsightType.UYARI, kaynak_tip='sofor', kaynak_id=sid, 
                                        mesaj=f"{ad}: Kritik performans düşüşü ({puan}/100)", onem_puani=85))
            
            # Tasarruf potansiyeli onersi
            if eval.filo_karsilastirma < -10:
                insights.append(Insight(tip=InsightType.ONERI, kaynak_tip='sofor', kaynak_id=sid, 
                                        mesaj=f"{ad}: Ekonomik sürüş eğitimi planlanabilir", onem_puani=55))

        return insights

    async def generate_fleet_insights(self) -> List[Insight]:
        """Filo geneli trendleri analiz et"""
        insights = []
        uow = get_uow()
        
        async with uow:
            stats = await uow.analiz_repo.get_monthly_comparison_stats()
            if not stats: return []
            
            tuketim_degisim = stats.get('tuketim_degisim', 0)
            if abs(tuketim_degisim) > 5:
                msg = f"Filo: Ortalama tüketim geçen aya göre %{abs(tuketim_degisim):.1f} {'arttı' if tuketim_degisim > 0 else 'azaldı'}"
                insights.append(Insight(
                    tip=InsightType.UYARI if tuketim_degisim > 0 else InsightType.IYILESME,
                    kaynak_tip='filo', kaynak_id=None, mesaj=msg, onem_puani=70
                ))
                
        return insights

    async def generate_all_and_save(self) -> int:
        """Tüm sistemi analiz et ve Alert olarak kaydet (Parallel & Bulk)"""
        import asyncio
        all_insights = []
        
        # 1. Analizleri paralel çalıştır (True Async)
        fleet_task = self.generate_fleet_insights()
        vehicle_task = self.generate_vehicle_insights_bulk()
        driver_task = self.generate_driver_insights_bulk()

        results = await asyncio.gather(fleet_task, vehicle_task, driver_task)
        
        for res in results:
            all_insights.extend(res)
        
        # 2. Kaydet (Alerts tablosuna - Bulk Insert)
        return await self.save_insights_as_alerts(all_insights)

    async def save_insights_as_alerts(self, insights: List[Insight]) -> int:
        """Insight'ları sistem uyarısı (Alert) olarak kaydet (Bulk Insert)."""
        from app.database.repositories.analiz_repo import get_analiz_repo
        
        analiz_repo = get_analiz_repo()
        
        alerts_data = []
        for i in insights:
            severity = 'high' if i.onem_puani >= 75 else 'medium' if i.onem_puani >= 50 else 'low'
            alerts_data.append({
                "alert_type": "insight",
                "severity": severity,
                "title": f"Sistem Analizi: {i.tip.value.capitalize()}",
                "message": i.mesaj,
                "source_id": i.kaynak_id,
                "source_type": i.kaynak_tip
            })
            
        if not alerts_data:
            return 0
            
        try:
            count = await analiz_repo.bulk_create_alerts(alerts_data)
            logger.info(f"Generated and saved {count} insights/alerts (Bulk).")
            return count
        except Exception as e:
            logger.error(f"Failed to save insights as alerts (Bulk): {e}")
            return 0


# Thread-safe Singleton
_insight_engine: Optional[InsightEngine] = None
_insight_engine_lock = threading.Lock()


def get_insight_engine() -> InsightEngine:
    """Thread-safe singleton getter"""
    global _insight_engine
    if _insight_engine is None:
        with _insight_engine_lock:
            if _insight_engine is None:
                _insight_engine = InsightEngine()
    return _insight_engine
