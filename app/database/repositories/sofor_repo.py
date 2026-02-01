"""
TIR Yakıt Takip - Şoför Repository
Şoför CRUD + performans sorguları
"""

from datetime import date
from typing import Dict, List, Optional

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
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Tüm şoförleri getir (Arama ve Sayfalama destekli).
        """
        _filters = filters.copy() if filters else {}
        if search:
            _filters["search"] = search

        return await super().get_all(
            filters=_filters,
            order_by="ad_soyad",
            limit=limit,
            offset=offset,
            include_inactive=not sadece_aktif
        )

    async def add(
        self,
        ad_soyad: str,
        telefon: str = "",
        ise_baslama: Optional[str] = None,
        ehliyet_sinifi: str = "E",
        score: float = 1.0,
        manual_score: float = 1.0,
        hiz_disiplin_skoru: float = 1.0,
        agresif_surus_faktoru: float = 1.0,
        notlar: str = ""
    ) -> int:
        """
        Yeni şoför ekle (TOCTOU Korumalı).
        """
        if ise_baslama and isinstance(ise_baslama, str) and ise_baslama.strip():
            try:
                ise_baslama_obj = date.fromisoformat(ise_baslama)
            except ValueError:
                logger.warning(f"Invalid date format: {ise_baslama}")
                ise_baslama_obj = None
        elif isinstance(ise_baslama, date):
            ise_baslama_obj = ise_baslama
        else:
            ise_baslama_obj = None

        async with self._get_session() as session:
            # 1. Kayıt var mı kontrol et ve kilitle
            from sqlalchemy import select
            stmt = select(self.model).where(self.model.ad_soyad == ad_soyad).with_for_update()
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.warning(f"TOCTOU Alert: Şoför zaten mevcut ({ad_soyad})")
                raise ValueError(f"Bu isimle şoför zaten kayıtlı: {ad_soyad}")

            # 2. Kaydı oluştur
            new_sofor = self.model(
                ad_soyad=ad_soyad,
                telefon=telefon,
                ise_baslama=ise_baslama_obj,
                ehliyet_sinifi=ehliyet_sinifi,
                score=score,
                manual_score=manual_score,
                hiz_disiplin_skoru=hiz_disiplin_skoru,
                agresif_surus_faktoru=agresif_surus_faktoru,
                notlar=notlar,
                aktif=True
            )
            session.add(new_sofor)
            
            if not self.session:
                await session.commit()
                await session.refresh(new_sofor)
            else:
                await session.flush()
            
            return new_sofor.id

    async def get_sefer_stats(
        self,
        sofor_id: int = None,
        baslangic: str = None,
        bitis: str = None
    ) -> List[Dict]:
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
            WHERE 1=1
        """
        params = {}

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
        self,
        sofor_id: int = None,
        limit: int = None
    ) -> List[Dict]:
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
            WHERE s.tuketim IS NOT NULL AND s.tuketim > 0
        """
        params = {}

        if sofor_id:
            query += " AND s.sofor_id = :sofor_id"
            params["sofor_id"] = sofor_id

        query += " GROUP BY s.sofor_id, sf.ad_soyad ORDER BY tuketim ASC"

        if limit:
            query += " LIMIT :limit"
            params["limit"] = limit

        return await self.execute_query(query, params)

    async def get_guzergah_performansi(self, sofor_id: int) -> List[Dict]:
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

    async def get_driver_consumptions(self, sofor_id: int, limit: int = 100) -> List[float]:
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
        return [row['tuketim'] for row in rows]

    async def get_by_name(self, ad_soyad: str) -> Optional[Dict]:
        """İsim ile şoför getir (Performans için)"""
        from sqlalchemy import select
        async with self._get_session() as session:
            stmt = select(self.model).where(self.model.ad_soyad == ad_soyad)
            result = await session.execute(stmt)
            return self._to_dict(result.scalar_one_or_none())

    async def get_aktif_isimler(self) -> List[str]:
        """Aktif şoför isimlerini getir"""
        query = "SELECT ad_soyad FROM soforler WHERE aktif = true ORDER BY ad_soyad"
        rows = await self.execute_query(query)
        return [row['ad_soyad'] for row in rows]


# Thread-safe Singleton
import threading
from sqlalchemy.ext.asyncio import AsyncSession

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
