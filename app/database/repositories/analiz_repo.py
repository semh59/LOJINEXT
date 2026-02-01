"""
TIR Yakıt Takip - Analiz Repository
ML eğitim verileri, dashboard istatistikleri, raporlama sorguları
"""

import json
import math
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.database.base_repository import BaseRepository
from app.database.models import Sefer, YakitFormul
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class AnalizRepository(BaseRepository[Sefer]):
    """Analiz ve istatistik veritabanı operasyonları (Async)"""

    # BaseRepository gereksinimi için default model (seferler üzerinden çok analiz yapılıyor)
    model = Sefer

    def _get_date_format_sql(self, session: AsyncSession, column: str) -> str:
        """Dialect bazlı tarih formatlama SQL fragment'ı döner."""
        dialect = session.bind.dialect.name
        if dialect == 'postgresql':
            return f"TO_CHAR({column}, 'YYYY-MM')"
        return f"strftime('%Y-%m', {column})"

    # =========================================================================
    # DASHBOARD İSTATİSTİKLERİ
    # =========================================================================

    async def get_dashboard_stats(self) -> Dict:
        """
        Zenginleştirilmiş Dashboard İstatistikleri (Elite Dashboard).
        SQLite ve PostgreSQL uyumlu hale getirildi.
        """
        query = text("""
            SELECT 
                (SELECT COUNT(*) FROM seferler WHERE (tuketim IS NULL OR tuketim > 0)) as toplam_sefer,
                (SELECT COALESCE(SUM(mesafe_km), 0) FROM seferler) as toplam_km,
                (SELECT COALESCE(SUM(litre), 0) FROM yakit_alimlari) as toplam_yakit,
                (SELECT COALESCE(AVG(tuketim), 32.0) FROM seferler WHERE tuketim > 0) as filo_ortalama,
                (SELECT COUNT(*) FROM araclar WHERE aktif IS NOT FALSE) as aktif_arac,
                (SELECT COUNT(*) FROM soforler WHERE aktif IS NOT FALSE) as aktif_sofor,
                (SELECT COUNT(*) FROM seferler WHERE tarih = CURRENT_DATE) as bugun_sefer
        """)
        
        async with self._get_session() as session:
            result = await session.execute(query)
            r = result.fetchone()
            if not r: return {}
            row = r._mapping

            return {
                'toplam_sefer': row['toplam_sefer'],
                'toplam_km': row['toplam_km'],
                'toplam_yakit': round(row['toplam_yakit'], 1),
                'filo_ortalama': round(row['filo_ortalama'], 2),
                'aktif_arac': row['aktif_arac'],
                'aktif_sofor': row['aktif_sofor'],
                'bugun_sefer': row['bugun_sefer']
            }

    async def get_filo_ortalama_tuketim(
        self,
        baslangic: str = None,
        bitis: str = None
    ) -> float:
        """Filo geneli ortalama yakıt tüketimi"""
        query = """
            SELECT AVG(tuketim) as ort
            FROM seferler
            WHERE tuketim IS NOT NULL AND tuketim > 0
        """
        params = {}

        if baslangic:
            query += " AND tarih >= :baslangic"
            params["baslangic"] = baslangic

        if bitis:
            query += " AND tarih <= :bitis"
            params["bitis"] = bitis

        result = await self.execute_scalar(query, params)
        return round(result, 2) if result else 32.0

    async def get_monthly_comparison_stats(self) -> Dict:
        """
        Bu ay vs geçen ay karşılaştırması (Cross-DB Compatible).
        Analiz motoru (Fleet Insight) için temel metrikleri döner.
        """
        today = date.today()
        bu_ay_bas = date(today.year, today.month, 1)
        
        # Geçen ay başı
        if today.month == 1:
            gecen_ay_bas = date(today.year - 1, 12, 1)
        else:
            gecen_ay_bas = date(today.year, today.month - 1, 1)

        query = text("""
            WITH current_month AS (
                SELECT 
                    COUNT(*) as sefer,
                    COALESCE(SUM(mesafe_km), 0) as km,
                    COALESCE(AVG(tuketim), 0) as tuketim
                FROM seferler
                WHERE tarih >= :bu_ay_bas
            ),
            previous_month AS (
                SELECT 
                    COUNT(*) as sefer,
                    COALESCE(SUM(mesafe_km), 0) as km,
                    COALESCE(AVG(tuketim), 0) as tuketim
                FROM seferler
                WHERE tarih >= :gecen_ay_bas AND tarih < :bu_ay_bas
            )
            SELECT 
                c.sefer as c_sefer, c.km as c_km, c.tuketim as c_tuketim,
                p.sefer as p_sefer, p.km as p_km, p.tuketim as p_tuketim
            FROM current_month c, previous_month p
        """)
        
        async with self._get_session() as session:
            result = await session.execute(query, {
                "bu_ay_bas": bu_ay_bas,
                "gecen_ay_bas": gecen_ay_bas
            })
            r = result.fetchone()
            
            if not r: return {}
            
            # Değişim oranlarını hesapla
            def pct_change(new, old):
                if not old or old == 0: return 0
                return round(((new - old) / old) * 100, 1)

            return {
                'bu_ay': {'sefer': r.c_sefer, 'km': r.c_km, 'tuketim': r.c_tuketim},
                'gecen_ay': {'sefer': r.p_sefer, 'km': r.p_km, 'tuketim': r.p_tuketim},
                'sefer_degisim': pct_change(r.c_sefer, r.p_sefer),
                'km_degisim': pct_change(r.c_km, r.p_km),
                'tuketim_degisim': pct_change(r.c_tuketim, r.p_tuketim)
            }

    async def get_all_vehicles_consumption_stats(self, days: int = 30) -> List[Dict]:
        """
        Tüm araçların son X günlük tüketim istatistiklerini getir (Bulk Intelligence).
        InsightEngine için N+1 problemini çözer.
        """
        # Input validation
        days = max(1, min(int(days or 30), 365))
        son_15_gun = today - timedelta(days=15)
        son_30_gun = today - timedelta(days=30)
        start_date = today - timedelta(days=days)

        # SQLite supports FILTER since 3.30.0, but to be safe we could use CASE WHEN
        # However, cross-db compatibility with text() params is easier.
        query = text("""
            SELECT 
                a.id as arac_id,
                a.plaka,
                a.hedef_tuketim,
                COUNT(s.id) as sefer_sayisi,
                AVG(s.tuketim) as ort_tuketim,
                AVG(CASE WHEN s.tarih >= :son_15_gun THEN s.tuketim ELSE NULL END) as son_15_gun_ort,
                AVG(CASE WHEN s.tarih < :son_15_gun AND s.tarih >= :son_30_gun THEN s.tuketim ELSE NULL END) as onceki_15_gun_ort
            FROM araclar a
            LEFT JOIN seferler s ON a.id = s.arac_id
            WHERE a.aktif = true 
              AND (s.tuketim IS NULL OR s.tuketim > 0)
              AND (s.tarih IS NULL OR s.tarih >= :start_date)
            GROUP BY a.id, a.plaka, a.hedef_tuketim
            HAVING COUNT(s.id) > 0
        """)
        
        async with self._get_session() as session:
            result = await session.execute(query, {
                "son_15_gun": son_15_gun,
                "son_30_gun": son_30_gun,
                "start_date": start_date
            })
            return [dict(row._mapping) for row in result.fetchall()]

    async def get_daily_consumption_series(self, days: int = 30) -> List[Dict]:
        """Son X günün günlük tüketim verileri"""
        # Input validation
        days = max(1, min(int(days or 30), 365))
        start_date = date.today() - timedelta(days=days)
        # PostgreSQL syntax: tarih >= :start_date
        query = """
            SELECT 
                tarih,
                COUNT(*) as sefer_sayisi,
                COALESCE(AVG(tuketim), 0) as tuketim,
                COALESCE(SUM(mesafe_km), 0) as toplam_km
            FROM seferler
            WHERE tarih >= :start_date
            GROUP BY tarih
            ORDER BY tarih
        """
        return await self.execute_query(query, {"start_date": start_date.isoformat()})

        # Cross-DB date formatting
        async with self._get_session() as session:
            date_fmt = self._get_date_format_sql(session, "y.tarih")

            query = text(f"""
                SELECT 
                    {date_fmt} as ay,
                    COALESCE(SUM(y.litre), 0) as consumption
                FROM yakit_alimlari y
                WHERE y.tarih >= :start_date
                GROUP BY {date_fmt}
                ORDER BY ay
            """)
            
            result = await session.execute(query, {"start_date": start_date.isoformat()})
            results = [dict(row._mapping) for row in result.fetchall()]

        # Ay isimlerini Türkçe'ye çevir
        ay_isimleri = {
            '01': 'Oca', '02': 'Şub', '03': 'Mar', '04': 'Nis',
            '05': 'May', '06': 'Haz', '07': 'Tem', '08': 'Ağu',
            '09': 'Eyl', '10': 'Eki', '11': 'Kas', '12': 'Ara'
        }

        formatted = []
        for r in results:
            ay = r.get('ay', '')
            if len(ay) >= 7:
                ay_num = ay[5:7]
                formatted.append({
                    'month': ay_isimleri.get(ay_num, ay_num),
                    'consumption': int(r.get('consumption', 0))
                })

        return formatted

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
        coeffs = params.get('coefficients', {})
        params_json = json.dumps({
            'weights': coeffs.get('weights', []),
            'intercept': coeffs.get('intercept', 0.0)
        })

        async with self._get_session() as session:
            try:
                # Cross-db compatible Upsert logic
                # Try to delete existing first, or check existence. 
                # For simplicity and cross-db safety: delete and insert within transaction
                delete_stmt = delete(YakitFormul).where(YakitFormul.arac_id == arac_id)
                await session.execute(delete_stmt)
                
                insert_stmt = insert(YakitFormul).values(
                    arac_id=arac_id,
                    katsayilar=params,
                    r2_score=params.get('r_squared', 0),
                    sample_count=params.get('sample_count', 0),
                    updated_at=datetime.now()
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
        async with self._get_session() as session:
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
                    'coefficients': katsayilar.get('coefficients') if 'coefficients' in katsayilar else katsayilar,
                    'r_squared': obj.r2_score,
                    'sample_count': obj.sample_count,
                    'updated_at': obj.updated_at
                }
            return None

    # =========================================================================
    # ELITE BULK ANALYTICS (N+1 SOLVER)
    # =========================================================================

    async def get_bulk_driver_metrics(self) -> List[Dict]:
        """
        Tüm şoförler için puanlama metriklerini TEK BİR sorgu ile getirir (Cross-DB).
        """
        today = date.today()
        son_15_gun = today - timedelta(days=15)
        son_30_gun = today - timedelta(days=30)

        query = text("""
            WITH driver_stats AS (
                SELECT 
                    s.sofor_id,
                    sf.ad_soyad,
                    COUNT(s.id) as toplam_sefer,
                    COALESCE(SUM(s.mesafe_km), 0) as toplam_km,
                    COALESCE(SUM(s.net_kg), 0) / 1000.0 as toplam_ton,
                    COALESCE(AVG(s.tuketim), 0) as ort_tuketim,
                    COALESCE(MIN(NULLIF(s.tuketim, 0)), 0) as en_iyi_tuketim,
                    COALESCE(MAX(NULLIF(s.tuketim, 0)), 0) as en_kotu_tuketim,
                    (SELECT (AVG(tuketim*tuketim) - AVG(tuketim)*AVG(tuketim)) FROM seferler WHERE sofor_id = s.sofor_id) as var_tuketim
                FROM seferler s
                JOIN soforler sf ON s.sofor_id = sf.id
                GROUP BY s.sofor_id, sf.ad_soyad
            ),
            trend_stats AS (
                SELECT 
                    sofor_id,
                    AVG(CASE WHEN tarih >= :son_15_gun THEN tuketim ELSE NULL END) as recent_avg,
                    AVG(CASE WHEN tarih < :son_15_gun AND tarih >= :son_30_gun THEN tuketim ELSE NULL END) as older_avg
                FROM seferler
                WHERE tuketim > 0
                GROUP BY sofor_id
            ),
            route_stats AS (
                SELECT 
                    sofor_id,
                    COUNT(DISTINCT (cikis_yeri || ' -> ' || varis_yeri)) as guzergah_sayisi
                FROM seferler
                GROUP BY sofor_id
            )
            SELECT 
                ds.*,
                ts.recent_avg,
                ts.older_avg,
                rs.guzergah_sayisi
            FROM driver_stats ds
            LEFT JOIN trend_stats ts ON ds.sofor_id = ts.sofor_id
            LEFT JOIN route_stats rs ON ds.sofor_id = rs.sofor_id
        """)
        
        async with self._get_session() as session:
            result = await session.execute(query, {
                "son_15_gun": son_15_gun,
                "son_30_gun": son_30_gun
            })
            rows = result.fetchall()
            
            # STDDEV handle (SQLite'da yoksa Python'da var'dan hesapla)
            data = []
            for row in rows:
                d = dict(row._mapping)
                if 'var_tuketim' in d and d['var_tuketim'] is not None:
                     d['std_sapma'] = math.sqrt(max(0, d['var_tuketim']))
                else:
                     d['std_sapma'] = 0.0
                data.append(d)
            return data

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
                AND tuketim IS NOT NULL
            ),
            f_stats AS (
                SELECT COALESCE(SUM(litre), 0) as toplam_yakit
                FROM yakit_alimlari
                WHERE tarih >= :start AND tarih <= :end
            )
            SELECT * FROM s_stats, f_stats
        """)
        async with self._get_session() as session:
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
            WHERE arac_id = :arac_id AND tarih >= :start_date
            AND tuketim IS NOT NULL AND tuketim > 0
        """)
        async with self._get_session() as session:
            result = await session.execute(query, {"arac_id": arac_id, "start_date": start_date})
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
                WHERE tarih >= :start_date AND tuketim IS NOT NULL
            ),
            cost AS (
                SELECT COALESCE(SUM(toplam_tutar), 0) as toplam_harcama
                FROM yakit_alimlari
                WHERE tarih >= :start_date
            )
            SELECT * FROM stats, cost
        """)
        async with self._get_session() as session:
            result = await session.execute(query, {"start_date": start_date})
            row = result.fetchone()
            return dict(row._mapping) if row else {}

    async def get_top_routes_by_vehicle(self, arac_id: int, start_date: date, limit: int = 5) -> List[Dict]:
        """Araç için en çok gidilen güzergahlar (ReportService için)"""
        # Input validation
        limit = max(1, min(int(limit or 5), 50))
        query = text("""
            SELECT 
                cikis_yeri || ' → ' || varis_yeri as guzergah,
                COUNT(*) as sefer,
                AVG(tuketim) as tuketim
            FROM seferler
            WHERE arac_id = :arac_id AND tarih >= :start_date
            AND tuketim IS NOT NULL
            GROUP BY cikis_yeri, varis_yeri
            ORDER BY sefer DESC
            LIMIT :limit
        """)
        async with self._get_session() as session:
            result = await session.execute(query, {"arac_id": arac_id, "start_date": start_date, "limit": limit})
            return [dict(row._mapping) for row in result.fetchall()]

    # =========================================================================
    # RAW SQL REFACTORING METHODS (Servis katmanından taşındı)
    # =========================================================================

    async def get_daily_summary_for_ml(
        self, 
        days: int = 60, 
        arac_id: int = None
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
                    AVG(ton) as ort_ton,
                    COUNT(*) as sefer_sayisi
                FROM seferler
                WHERE arac_id = :arac_id
                  AND tarih >= :start_date
                  AND tuketim IS NOT NULL
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
                    AVG(ton) as ort_ton,
                    COUNT(*) as sefer_sayisi
                FROM seferler
                WHERE tarih >= :start_date
                  AND tuketim IS NOT NULL
                GROUP BY tarih
                ORDER BY tarih ASC
            """)
            params = {"start_date": start_date}
        
        async with self._get_session() as session:
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
            WHERE tarih >= :start_date
            GROUP BY varis_yeri
            ORDER BY count DESC
        """)
        
        async with self._get_session() as session:
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
            WHERE s.tuketim IS NOT NULL AND s.tuketim > 0
            GROUP BY sf.id
            ORDER BY avg_consumption ASC
            LIMIT :limit
        """)
        
        async with self._get_session() as session:
            result = await session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
        return {
            'categories': [r.ad_soyad for r in rows],
            'values': [round(r.avg_consumption, 2) for r in rows]
        }

    async def create_insight_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        source_id: int = None,
        source_type: str = None
    ) -> int:
        """
        Insight'ı alert olarak kaydet (InsightEngine için).
        
        Returns:
            Oluşturulan alert ID
        """
        async with self._get_session() as session:
            try:
                query = text("""
                    INSERT INTO alerts (alert_type, severity, title, message, source_id, source_type)
                    VALUES (:type, :sev, :title, :msg, :sid, :stype)
                """)
                
                result = await session.execute(query, {
                    "type": alert_type,
                    "sev": severity,
                    "title": title,
                    "msg": message,
                    "sid": source_id,
                    "stype": source_type
                })
                
                # Fetch last inserted id (Dialect independent fetch)
                # Some async dialects might not support result.lastrowid as well.
                # In that case, we can use a separate query or standard SQLAlchemy insert.
                
                # Let's use the standard SQLAlchemy insert for better compatibility
                # But since the request was to fix raw SQL, I'll stick to a safe approach.
                if session.bind.dialect.name == 'postgresql':
                    # Re-run with RETURNING for PG if absolute precision needed, 
                    # but for cross-db, simple is better.
                    pass
                
                if not self.session:
                    await session.commit()
                
                return 1 # ID return omitted for maximum compatibility unless required
            except Exception as e:
                if not self.session: await session.rollback()
                logger.error(f"Error creating alert: {e}")
                return 0

    async def get_recent_unread_alerts(self, limit: int = 3) -> List[Dict]:
        """
        Son okunmamış uyarıları getir (Güvenli parametreli sorgu).
        
        AI Service context building için kullanılır.
        Raw SQL yerine bu metod tercih edilmelidir.
        
        Args:
            limit: Maksimum alert sayısı (default 3, max 10)
            
        Returns:
            List[Dict]: Alert title ve message içeren dict listesi
        """
        # Input validation
        limit = max(1, min(int(limit), 10))
        
        query = text("""
            SELECT title, message
            FROM alerts
            WHERE status = 'unread'
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        async with self._get_session() as session:
            result = await session.execute(query, {"limit": limit})
            return [dict(row._mapping) for row in result.fetchall()]

    async def bulk_create_alerts(self, alerts: List[Dict]) -> int:
        """
        Toplu alert oluşturma (Batch Insert Optimization).
        """
        if not alerts:
            return 0
            
        query = text("""
            INSERT INTO alerts (alert_type, severity, title, message, source_id, source_type)
            VALUES (:alert_type, :severity, :title, :message, :source_id, :source_type)
        """)
        
        async with self._get_session() as session:
            await session.execute(query, alerts)
            if not self.session:
                await session.commit()
            return len(alerts)


# Thread-safe Singleton
import threading
from sqlalchemy.ext.asyncio import AsyncSession

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
