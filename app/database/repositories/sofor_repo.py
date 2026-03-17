"""
TIR Yakıt Takip - Şoför Repository
PostgreSQL CRUD + performans sorguları
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import threading

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.database.models import Sofor
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SoforRepository(BaseRepository[Sofor]):
    """Şoför veritabanı operasyonları (Async)"""

    model = Sofor
    search_columns = ["ad_soyad", "telefon"]

    async def get_all(
        self,
        sadece_aktif: bool = True,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Tüm şoförleri getir (Arama ve Sayfalama destekli).
        """
        _filters = filters.copy() if filters else {}
        if search:
            _filters["search"] = search

        # Soft delete filtresi (varsayılan: silinmemişler)
        if "is_deleted" not in _filters:
            _filters["is_deleted"] = False

        return await super().get_all(
            filters=_filters,
            order_by="ad_soyad",
            limit=limit,
            offset=offset,
            include_inactive=not sadece_aktif,
        )

    async def count_all(
        self,
        sadece_aktif: bool = True,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Filtrelere uyan toplam şoför sayısını getir"""
        _filters = filters.copy() if filters else {}
        if search:
            _filters["search"] = search
        if "is_deleted" not in _filters:
            _filters["is_deleted"] = False

        return await super().count(
            filters=_filters,
            include_inactive=not sadece_aktif,
        )

    async def add(
        self,
        ad_soyad: str,
        telefon: str = "",
        ise_baslama: Optional[date] = None,
        ehliyet_sinifi: str = "E",
        score: float = 1.0,
        manual_score: float = 1.0,
        hiz_disiplin_skoru: float = 1.0,
        agresif_surus_faktoru: float = 1.0,
        notlar: str = "",
    ) -> int:
        """
        Yeni şoför ekle (TOCTOU Korumalı).
        """
        session = self.session
        # 1. Kayıt var mı kontrol et ve kilitle
        stmt = (
            select(self.model).where(self.model.ad_soyad == ad_soyad).with_for_update()
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            logger.warning("TOCTOU Alert: Şoför zaten mevcut.")
            raise ValueError(
                "Bu isimle şoför zaten kayıtlı. Lütfen farklı bir isim deneyin."
            )

        # 2. Kaydı oluştur
        new_sofor = self.model(
            ad_soyad=ad_soyad,
            telefon=telefon,
            ise_baslama=ise_baslama,
            ehliyet_sinifi=ehliyet_sinifi,
            score=score,
            manual_score=manual_score,
            hiz_disiplin_skoru=hiz_disiplin_skoru,
            agresif_surus_faktoru=agresif_surus_faktoru,
            notlar=notlar,
            aktif=True,
        )
        session.add(new_sofor)

        if not self.session:
            await session.commit()
            await session.refresh(new_sofor)
        else:
            await session.flush()

        return int(new_sofor.id)

    async def get_sefer_stats(
        self,
        sofor_id: Optional[int] = None,
        baslangic: Optional[date] = None,
        bitis: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Şoför bazlı sefer istatistikleri (Zenginleştirilmiş).
        N+1 problemini çözmek için tüm metrikleri tek bir JOIN/GROUP BY ile getirir.
        """
        query = """
            SELECT 
                s.sofor_id,
                sf.ad_soyad,
                COUNT(s.id) as toplam_sefer,
                COALESCE(SUM(s.mesafe_km), 0) as toplam_km,
                COALESCE(SUM(s.net_kg), 0) / 1000.0 as toplam_ton,
                SUM(CASE WHEN s.bos_sefer = true THEN 1 ELSE 0 END) as bos_sefer_sayisi,
                COALESCE(SUM(s.dagitilan_yakit), 0) as toplam_yakit,
                COALESCE(AVG(s.tuketim), 0.0) as ort_tuketim,
                MIN(NULLIF(s.tuketim, 0)) as en_iyi_tuketim,
                MAX(NULLIF(s.tuketim, 0)) as en_kotu_tuketim
            FROM seferler s
            JOIN soforler sf ON s.sofor_id = sf.id
            WHERE sf.is_deleted = false AND s.is_deleted = false
        """
        params: Dict[str, Any] = {}

        if sofor_id:
            query += " AND s.sofor_id = :sofor_id"
            params["sofor_id"] = sofor_id

        if baslangic:
            query += " AND s.tarih >= :baslangic"
            params["baslangic"] = baslangic

        if bitis:
            query += " AND s.tarih <= :bitis"
            params["bitis"] = bitis

        query += " GROUP BY s.sofor_id, sf.ad_soyad ORDER BY toplam_sefer DESC"

        return await self.execute_query(query, params)

    async def get_yakit_tuketimi(
        self, sofor_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Şoför bazlı yakıt tüketimi (seferler üzerinden).
        """
        query = """
            SELECT 
                s.sofor_id,
                sf.ad_soyad,
                COUNT(s.id) as sefer_sayisi,
                SUM(s.mesafe_km) as toplam_km,
                SUM(s.dagitilan_yakit) as dagitilan_yakit,
                AVG(s.tuketim) as tuketim
            FROM seferler s
            JOIN soforler sf ON s.sofor_id = sf.id
            WHERE sf.is_deleted = false AND s.is_deleted = false 
              AND s.tuketim IS NOT NULL AND s.tuketim > 0
        """
        params: Dict[str, Any] = {}

        if sofor_id:
            query += " AND s.sofor_id = :sofor_id"
            params["sofor_id"] = sofor_id

        query += " GROUP BY s.sofor_id, sf.ad_soyad ORDER BY tuketim ASC"

        if limit:
            query += " LIMIT :limit"
            params["limit"] = limit

        return await self.execute_query(query, params)

    async def get_guzergah_performansi(self, sofor_id: int) -> List[Dict[str, Any]]:
        """
        Şoförün güzergah bazlı performansı.
        """
        query = """
            SELECT 
                s.cikis_yeri || ' → ' || s.varis_yeri as guzergah,
                COUNT(*) as sefer_sayisi,
                SUM(s.mesafe_km) as toplam_km,
                AVG(s.tuketim) as ort_tuketim,
                MIN(s.tuketim) as en_iyi,
                MAX(s.tuketim) as en_kotu
            FROM seferler s
            WHERE s.sofor_id = :sofor_id AND s.tuketim IS NOT NULL AND s.tuketim > 0
            GROUP BY s.cikis_yeri, s.varis_yeri
            ORDER BY sefer_sayisi DESC
        """
        return await self.execute_query(query, {"sofor_id": sofor_id})

    async def get_driver_consumptions(
        self, sofor_id: int, limit: int = 100
    ) -> List[float]:
        """
        Şoförün son seferlerindeki tüketim değerleri (Trend ve StdDev için).
        """
        query = """
            SELECT tuketim FROM seferler 
            WHERE sofor_id = :sofor_id AND tuketim IS NOT NULL AND tuketim > 0
            ORDER BY tarih DESC
            LIMIT :limit
        """
        rows = await self.execute_query(query, {"sofor_id": sofor_id, "limit": limit})
        return [row["tuketim"] for row in rows]

    async def get_by_name(
        self, ad_soyad: str, for_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        """İsim ile şoför getir (Performans için)"""
        session = self.session
        stmt = select(self.model).where(
            self.model.ad_soyad == ad_soyad, self.model.is_deleted.is_(False)
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()
        return dict(obj.__dict__) if obj else None

    async def get_aktif_isimler(self) -> List[str]:
        """Aktif şoför isimlerini getir"""
        query = "SELECT ad_soyad FROM soforler WHERE aktif = true AND is_deleted = false ORDER BY ad_soyad"
        rows = await self.execute_query(query)
        return [str(row["ad_soyad"]) for row in rows]

    async def get_driver_anomalies_count(
        self, sofor_id: int, days: int = 30
    ) -> Dict[str, int]:
        """
        Şoförün anomalilerini say (Sefer bazlı + Şoför bazlı).
        Ciddiyet seviyelerine göre gruplar.
        """
        cutoff_date = date.today() - timedelta(days=days)

        query = """
            SELECT 
                a.severity,
                COUNT(a.id) as count
            FROM anomalies a
            LEFT JOIN seferler s ON a.kaynak_id = s.id AND a.kaynak_tip = 'sefer'
            WHERE 
                (s.sofor_id = :sofor_id OR (a.kaynak_tip = 'sofor' AND a.kaynak_id = :sofor_id))
                AND a.tarih >= :cutoff_date
            GROUP BY a.severity
        """
        rows = await self.execute_query(
            query, {"sofor_id": sofor_id, "cutoff_date": cutoff_date}
        )

        result = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for row in rows:
            sev = row["severity"]
            # Enum value might be returned as string
            if hasattr(sev, "value"):
                sev = sev.value
            if sev in result:
                result[sev] = row["count"]

        return result

    async def bulk_soft_delete(
        self, ids: List[int], current_user_id: Optional[int] = None
    ) -> int:
        """
        Toplu soft silme (Performanslı).
        """
        if not ids:
            return 0

        return await self.bulk_update(ids=ids, is_deleted=True, aktif=False)


_sofor_repo_lock = threading.Lock()
_sofor_repo: Optional[SoforRepository] = None


def get_sofor_repo(session: Optional[AsyncSession] = None) -> SoforRepository:
    """SoforRepo Provider. Eğer session verilirse yeni instance döner (UoW için)."""
    global _sofor_repo
    if session:
        return SoforRepository(session=session)
    with _sofor_repo_lock:
        if _sofor_repo is None:
            _sofor_repo = SoforRepository()
    return _sofor_repo
