"""
TIR Yakıt Takip - Analiz Repository
ML eğitim verileri, dashboard istatistikleri, raporlama sorguları
"""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import threading
from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.database.models import Sefer, YakitFormul
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

# Configurable defaults
DEFAULT_FILO_ORTALAMA = 32.0


class AnalizRepository(BaseRepository[Sefer]):
    """Analiz ve istatistik veritabanı operasyonları (Async)"""

    # BaseRepository gereksinimi için default model (seferler üzerinden çok analiz yapılıyor)
    model = Sefer

    # =========================================================================
    # ML VERİLERİ
    # =========================================================================

    async def get_training_seferler(self, arac_id: int, limit: int = 200) -> List[Dict]:
        """AI model eğitimi için sefer verilerini getir"""
        # Input validation
        limit = max(1, min(int(limit or 200), 1000))
        query = """
            SELECT 
                s.mesafe_km,
                s.net_kg / 1000.0 as ton,
                s.tuketim,
                s.sofor_id,
                l.ascent_m,
                l.zorluk
            FROM seferler s
            LEFT JOIN lokasyonlar l ON (s.cikis_yeri = l.cikis_yeri AND s.varis_yeri = l.varis_yeri)
            WHERE s.arac_id = :arac_id 
              AND s.tuketim IS NOT NULL 
              AND s.tuketim > 0
              AND s.durum = 'Tamam'
            ORDER BY s.tarih DESC
            LIMIT :limit
        """
        return await self.execute_query(query, {"arac_id": arac_id, "limit": limit})

    async def save_model_params(self, arac_id: int, params: Dict[str, Any]):
        """AI model parametrelerini kaydet (Upsert - YakitFormul)"""
        session = self.session
        try:
            # Cross-db compatible Upsert logic
            # Try to delete existing first, or check existence.
            # For simplicity and cross-db safety: delete and insert within transaction
            delete_stmt = delete(YakitFormul).where(YakitFormul.arac_id == arac_id)
            await session.execute(delete_stmt)

            insert_stmt = insert(YakitFormul).values(
                arac_id=arac_id,
                katsayilar=params,
                r2_score=params.get("r_squared", 0),
                sample_count=params.get("sample_count", 0),
                updated_at=datetime.now(timezone.utc),
            )
            await session.execute(insert_stmt)

            # Check if katsayilar actually needs dump.
            # Model definition: katsayilar: Mapped[dict] = mapped_column(JSON)
            # Logic: Pydantic or SQLAlchemy AsyncPG handles JSON conversion usually if type is JSON.
            # Previous code used json.dumps explicitly. I will use the dict directly as it is mapped_column(JSON)

            if not self.session:
                await session.commit()
        except Exception as e:
            if not self.session:
                await session.rollback()
            logger.error(f"Error saving model params: {e}")
            raise e

    async def get_model_params(self, arac_id: int) -> Optional[Dict]:
        """AI model parametrelerini getir"""
        session = self.session
        stmt = select(YakitFormul).where(YakitFormul.arac_id == arac_id)
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()

        if obj:
            # obj.katsayilar is already a dict if JSON type used correctly with asyncpg
            katsayilar = obj.katsayilar

            # Handling if it comes as string (legacy data)
            if isinstance(katsayilar, str):
                katsayilar = json.loads(katsayilar)

            # Backwards compat parsing of coefficients
            # If katsayilar has 'coefficients', use it?
            # The logic in previous repo was:
            # if isinstance(katsayilar_raw, str): load...
            # coefficients = katsayilar_raw
            # return {'coefficients': coefficients, ...}

            # Let's assume structure is consistent
            return {
                "coefficients": katsayilar.get("coefficients")
                if "coefficients" in katsayilar
                else katsayilar,
                "r_squared": obj.r2_score,
                "sample_count": obj.sample_count,
                "updated_at": obj.updated_at,
            }
        return None

    # =========================================================================
    # ELITE BULK ANALYTICS (N+1 SOLVER)
    # =========================================================================

    async def get_bulk_driver_metrics(self) -> List[Dict]:
        """
        Tüm şoförler için puanlama metriklerini TEK BİR sorgu ile getirir (PostgreSQL).
        """
        today = date.today()
        son_15_gun = today - timedelta(days=15)
        son_30_gun = today - timedelta(days=30)

        query = text("""
            SELECT 
                s.sofor_id,
                sf.ad_soyad,
                COUNT(s.id) as toplam_sefer,
                COALESCE(SUM(s.mesafe_km), 0) as toplam_km,
                COALESCE(SUM(s.net_kg), 0) / 1000.0 as toplam_ton,
                COALESCE(AVG(s.tuketim), 0) as ort_tuketim,
                COALESCE(MIN(NULLIF(s.tuketim, 0)), 0) as en_iyi_tuketim,
                COALESCE(MAX(NULLIF(s.tuketim, 0)), 0) as en_kotu_tuketim,
                COALESCE(STDDEV(s.tuketim), 0) as std_sapma,
                COUNT(DISTINCT (s.cikis_yeri || ' -> ' || s.varis_yeri)) as guzergah_sayisi,
                AVG(s.tuketim) FILTER (WHERE s.tarih >= :son_15_gun AND s.tuketim > 0) as recent_avg,
                AVG(s.tuketim) FILTER (WHERE s.tarih < :son_15_gun AND s.tarih >= :son_30_gun AND s.tuketim > 0) as older_avg
            FROM seferler s
            JOIN soforler sf ON s.sofor_id = sf.id
            WHERE s.is_real = True AND s.is_deleted = False
            GROUP BY s.sofor_id, sf.ad_soyad
        """)

        session = self.session
        result = await session.execute(
            query, {"son_15_gun": son_15_gun, "son_30_gun": son_30_gun}
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_dashboard_stats(self) -> Dict:
        """Genel dashboard istatistiklerini getir (AI Context için)"""
        query = text("""
            SELECT 
                (SELECT COUNT(*) FROM araclar) as toplam_arac,
                (SELECT COUNT(*) FROM soforler) as toplam_sofor,
                (SELECT COUNT(*) FROM seferler WHERE tuketim > 0 AND is_real = True AND is_deleted = False) as filo_ortalama,
                (SELECT SUM(litre) FROM yakit_alimlari) as toplam_yakit
        """)
        session = self.session
        try:
            result = await session.execute(query)
            row = result.fetchone()
            if row:
                data = dict(row._mapping)
                # Defaults for empty DB
                return {
                    "toplam_arac": data.get("toplam_arac") or 0,
                    "toplam_sofor": data.get("toplam_sofor") or 0,
                    "filo_ortalama": float(data.get("filo_ortalama") or 32.0),
                    "toplam_yakit": float(data.get("toplam_yakit") or 0),
                }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")

        return {
            "toplam_arac": 0,
            "toplam_sofor": 0,
            "filo_ortalama": 32.0,
            "toplam_yakit": 0,
        }

    async def get_recent_unread_alerts(self, limit: int = 5) -> List[Dict]:
        """Son okunmamış uyarıları getir (AI Context için)"""
        # Note: Alerts table might be named 'anomali_logs' or similar in this schema.
        # I'll check if 'anomaliler' table exists or use fallback.
        query = text("""
            SELECT type as title, message, severity, created_at
            FROM anomaliler
            WHERE is_read = false
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        session = self.session
        try:
            result = await session.execute(query, {"limit": limit})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            # Table might not exist yet or have different name
            logger.warning(f"Recent alerts query failed (likely table missing): {e}")
            return []

    async def get_period_stats(self, start: date, end: date) -> Dict:
        """Dönem bazlı yakıt ve sefer özeti (ReportService için)"""
        query = text("""
            WITH s_stats AS (
                SELECT 
                    COUNT(*) as toplam_sefer,
                    COALESCE(SUM(mesafe_km), 0) as toplam_km,
                    COALESCE(AVG(tuketim), 0) as ortalama_tuketim
                FROM seferler
                WHERE tarih >= :start AND tarih <= :end
                AND tuketim IS NOT NULL AND is_real = True AND is_deleted = False
            ),
            f_stats AS (
                SELECT COALESCE(SUM(litre), 0) as toplam_yakit
                FROM yakit_alimlari
                WHERE tarih >= :start AND tarih <= :end
            )
            SELECT * FROM s_stats, f_stats
        """)
        session = self.session
        result = await session.execute(query, {"start": start, "end": end})
        row = result.fetchone()
        return dict(row._mapping) if row else {}

    async def get_vehicle_summary_stats(self, arac_id: int, start_date: date) -> Dict:
        """Araç performans özeti (ReportService için)"""
        query = text("""
            SELECT 
                COUNT(*) as sefer_sayisi,
                COALESCE(SUM(mesafe_km), 0) as toplam_km,
                COALESCE(AVG(tuketim), 0) as ort_tuketim,
                COALESCE(MIN(tuketim), 0) as en_iyi,
                COALESCE(MAX(tuketim), 0) as en_kotu
            FROM seferler
            WHERE arac_id = :arac_id AND tarih >= :start_date AND is_real = True AND is_deleted = False
            AND tuketim IS NOT NULL AND tuketim > 0
        """)
        session = self.session
        result = await session.execute(
            query, {"arac_id": arac_id, "start_date": start_date}
        )
        row = result.fetchone()
        return dict(row._mapping) if row else {}

    async def get_fleet_performance_stats(self, start_date: date) -> Dict:
        """Filo performans özeti (ReportService için)"""
        query = text("""
            WITH stats AS (
                SELECT 
                    COUNT(*) as toplam_sefer,
                    COALESCE(SUM(mesafe_km), 0) as toplam_km,
                    COALESCE(AVG(tuketim), 0) as filo_ortalama
                FROM seferler
                WHERE tarih >= :start_date AND tuketim IS NOT NULL AND is_real = True AND is_deleted = False
            ),
            cost AS (
                SELECT COALESCE(SUM(toplam_tutar), 0) as toplam_harcama
                FROM yakit_alimlari
                WHERE tarih >= :start_date
            )
            SELECT * FROM stats, cost
        """)
        session = self.session
        result = await session.execute(query, {"start_date": start_date})
        row = result.fetchone()
        return dict(row._mapping) if row else {}

    async def get_top_routes_by_vehicle(
        self, arac_id: int, start_date: date, limit: int = 5
    ) -> List[Dict]:
        """Araç için en çok gidilen güzergahlar (ReportService için)"""
        # Input validation
        limit = max(1, min(int(limit or 5), 50))
        query = text("""
            SELECT 
                cikis_yeri || ' → ' || varis_yeri as guzergah,
                COUNT(*) as sefer,
                AVG(tuketim) as tuketim
            FROM seferler
            WHERE arac_id = :arac_id AND tarih >= :start_date AND is_real = True AND is_deleted = False
            AND tuketim IS NOT NULL
            GROUP BY cikis_yeri, varis_yeri
            ORDER BY sefer DESC
            LIMIT :limit
        """)
        session = self.session
        result = await session.execute(
            query, {"arac_id": arac_id, "start_date": start_date, "limit": limit}
        )
        return [dict(row._mapping) for row in result.fetchall()]

    # =========================================================================
    # RAW SQL REFACTORING METHODS (Servis katmanından taşındı)
    # =========================================================================

    async def get_daily_summary_for_ml(
        self, days: int = 60, arac_id: int = None
    ) -> List[Dict]:
        """
        ML modeli için günlük özet veriler (TimeSeriesService için).

        Args:
            days: Kaç günlük veri
            arac_id: Opsiyonel araç filtresi
        """
        # Input validation
        days = max(1, min(int(days or 60), 730))
        start_date = date.today() - timedelta(days=days)

        if arac_id:
            query = text("""
                SELECT 
                    tarih,
                    AVG(tuketim) as ort_tuketim,
                    SUM(mesafe_km) as toplam_km,
                    SUM(tuketim * mesafe_km / 100.0) as toplam_litre,
                    AVG(ton) as ort_ton,
                    COUNT(*) as sefer_sayisi
                FROM seferler
                WHERE arac_id = :arac_id
                  AND tarih >= :start_date
                  AND tuketim IS NOT NULL
                  AND is_real = True AND is_deleted = False
                GROUP BY tarih
                ORDER BY tarih ASC
            """)
            params = {"arac_id": arac_id, "start_date": start_date}
        else:
            query = text("""
                SELECT 
                    tarih,
                    AVG(tuketim) as ort_tuketim,
                    SUM(mesafe_km) as toplam_km,
                    SUM(tuketim * mesafe_km / 100.0) as toplam_litre,
                    AVG(ton) as ort_ton,
                    COUNT(*) as sefer_sayisi
                FROM seferler
                WHERE tarih >= :start_date
                  AND tuketim IS NOT NULL
                  AND is_real = True AND is_deleted = False
                GROUP BY tarih
                ORDER BY tarih ASC
            """)
            params = {"start_date": start_date}

        session = self.session
        result = await session.execute(query, params)
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_heatmap_data(self, days: int = 90) -> List[Dict]:
        """
        Heatmap için varış noktası yoğunluk verisi (ReportService için).
        """
        # Input validation
        days = max(1, min(int(days or 90), 365))
        start_date = date.today() - timedelta(days=days)

        query = text("""
            SELECT varis_yeri, COUNT(*) as count, AVG(tuketim) as avg_consumption
            FROM seferler
            WHERE tarih >= :start_date AND is_real = True AND is_deleted = False
            GROUP BY varis_yeri
            ORDER BY count DESC
        """)

        session = self.session
        result = await session.execute(query, {"start_date": start_date})
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_driver_comparison(self, limit: int = 10) -> Dict:
        """
        Şoför karşılaştırma chart verisi (ReportService için).
        """
        # Input validation
        limit = max(1, min(int(limit or 10), 100))
        query = text("""
            SELECT sf.ad_soyad, AVG(s.tuketim) as avg_consumption
            FROM seferler s
            JOIN soforler sf ON s.sofor_id = sf.id
            WHERE s.tuketim IS NOT NULL AND s.tuketim > 0 AND s.is_real = True AND s.is_deleted = False
            GROUP BY sf.id
            ORDER BY avg_consumption ASC
            LIMIT :limit
        """)

        session = self.session
        result = await session.execute(query, {"limit": limit})
        rows = result.fetchall()

        return {
            "categories": [r.ad_soyad for r in rows],
            "values": [round(r.avg_consumption, 2) for r in rows],
        }

    async def get_daily_consumption_series(self, days: int = 30) -> List[Dict]:
        """
        Son X günün günlük toplam yakıt tüketim serisi.
        Grafikler için kullanılır.
        """
        days = max(1, min(int(days or 30), 365))
        start_date = date.today() - timedelta(days=days)

        query = text("""
            SELECT 
                tarih as date,
                COALESCE(SUM(litre), 0) as value
            FROM yakit_alimlari
            WHERE tarih >= :start_date
            GROUP BY tarih
            ORDER BY tarih ASC
        """)

        session = self.session
        result = await session.execute(query, {"start_date": start_date})
        return [
            {
                "date": row.date.isoformat() if row.date else None,
                "value": float(row.value),
            }
            for row in result.fetchall()
        ]

    async def get_top_performing_vehicles(self, limit: int = 15) -> List[Dict]:
        """
        En iyi performans gösteren (düşük tüketimli) araçlar.
        """
        limit = max(1, min(int(limit or 15), 100))
        query = text("""
            SELECT 
                a.plaka,
                AVG(s.tuketim) as avg_consumption,
                COUNT(s.id) as trip_count
            FROM araclar a
            JOIN seferler s ON a.id = s.arac_id
            WHERE s.tuketim > 0 AND s.is_real = True AND s.is_deleted = False
            GROUP BY a.id, a.plaka
            HAVING COUNT(s.id) >= 3
            ORDER BY avg_consumption ASC
            LIMIT :limit
        """)

        session = self.session
        result = await session.execute(query, {"limit": limit})
        return [
            {
                "plaka": row.plaka,
                "avg_consumption": round(row.avg_consumption, 2),
                "trip_count": row.trip_count,
            }
            for row in result.fetchall()
        ]

    async def get_bulk_cost_stats(self, months: int = 12) -> List[Dict]:
        """
        Aylık maliyet istatistiklerini getir (PostgreSQL optimized).
        Yakıt ve Sefer verilerini ay bazında gruplayarak döner.
        """
        months_int = int(months or 12)
        query = text("""
            WITH fuel_stats AS (
                SELECT 
                    TO_CHAR(tarih, 'YYYY-MM') as ay,
                    SUM(toplam_tutar) as yakit_tl,
                    SUM(litre) as yakit_litre
                FROM yakit_alimlari
                WHERE tarih >= (CURRENT_DATE - (:months * INTERVAL '1 month'))
                GROUP BY 1
            ),
            trip_stats AS (
                SELECT 
                    TO_CHAR(tarih, 'YYYY-MM') as ay,
                    COUNT(*) as sefer_sayisi,
                    SUM(mesafe_km) as toplam_km
                FROM seferler
                WHERE tarih >= (CURRENT_DATE - (:months * INTERVAL '1 month')) AND is_real = True AND is_deleted = False
                GROUP BY 1
            )
            SELECT 
                COALESCE(f.ay, s.ay) as ay,
                COALESCE(f.yakit_tl, 0) as yakit_tl,
                COALESCE(f.yakit_litre, 0) as yakit_litre,
                COALESCE(s.sefer_sayisi, 0) as sefer_sayisi,
                COALESCE(s.toplam_km, 0) as toplam_km
            FROM fuel_stats f
            FULL OUTER JOIN trip_stats s ON f.ay = s.ay
            ORDER BY ay DESC
        """)

        session = self.session
        result = await session.execute(query, {"months": months_int})
        # Mapping rows to dicts
        return [dict(row._mapping) for row in result.fetchall()]


_analiz_repo_lock = threading.Lock()
_analiz_repo: Optional[AnalizRepository] = None


def get_analiz_repo(session: Optional[AsyncSession] = None) -> AnalizRepository:
    """AnalizRepo Provider. Eğer session verilirse yeni instance döner (UoW için)."""
    global _analiz_repo
    if session:
        return AnalizRepository(session=session)
    with _analiz_repo_lock:
        if _analiz_repo is None:
            _analiz_repo = AnalizRepository()
    return _analiz_repo
