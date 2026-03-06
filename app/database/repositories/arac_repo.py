"""
TIR Yakıt Takip - Araç Repository
PostgreSQL CRUD operasyonları
"""

from typing import Any, Dict, List, Optional
import threading

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.database.models import Arac
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class AracRepository(BaseRepository[Arac]):
    """Araç veritabanı operasyonları (Async)"""

    model = Arac
    search_columns = ["plaka", "marka", "model"]

    async def get_all(
        self,
        sadece_aktif: bool = True,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Tüm araçları getir (Arama ve Sayfalama destekli).
        """
        _filters = filters.copy() if filters else {}
        if search:
            _filters["search"] = search

        return await self.get_all_with_stats_paged(
            limit=limit,
            offset=offset,
            search=search,
            filters=_filters,
            sadece_aktif=sadece_aktif,
        )

    async def get_all_with_stats_paged(
        self,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sadece_aktif: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Araçları istatistikleriyle (KM, Tüketim) beraber getirir.
        N+1 problemini çözer.
        """
        # Base Query
        query = """
            SELECT 
                a.*,
                COALESCE(SUM(s.mesafe_km), 0) as toplam_km,
                COUNT(s.id) as toplam_sefer,
                COALESCE(AVG(s.tuketim), 0.0) as ort_tuketim
            FROM araclar a
            LEFT JOIN seferler s ON a.id = s.arac_id AND s.tuketim IS NOT NULL
            WHERE 1=1
        """

        params = {}

        # Filters
        if sadece_aktif:
            query += " AND a.aktif = true"

        if search:
            query += " AND (a.plaka ILIKE :search OR a.marka ILIKE :search)"
            params["search"] = f"%{search}%"

        if filters:
            if "marka" in filters:
                query += " AND a.marka = :marka"
                params["marka"] = filters["marka"]
            if "model" in filters:
                query += " AND a.model = :model"
                params["model"] = filters["model"]
            if "yil_ge" in filters:
                query += " AND a.yil >= :yil_ge"
                params["yil_ge"] = filters["yil_ge"]
            if "yil_le" in filters:
                query += " AND a.yil <= :yil_le"
                params["yil_le"] = filters["yil_le"]

        # Group By & Order & Limit
        query += """
            GROUP BY a.id
            ORDER BY a.plaka ASC
            LIMIT :limit OFFSET :offset
        """

        params["limit"] = limit
        params["offset"] = offset

        return await self.execute_query(query, params)

    async def get_by_plaka(
        self, plaka: str, for_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Plaka ile araç getir"""
        session = self.session
        stmt = select(self.model).where(self.model.plaka == plaka)
        if for_update:
            stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()
        return dict(obj.__dict__) if obj else None

    async def add(
        self,
        plaka: str,
        marka: str,
        model: str = "",
        yil: int = 2020,
        tank_kapasitesi: int = 600,
        hedef_tuketim: float = 32.0,
        bos_agirlik_kg: float = 8000.0,
        hava_direnc_katsayisi: float = 0.7,
        on_kesit_alani_m2: float = 8.5,
        motor_verimliligi: float = 0.38,
        lastik_direnc_katsayisi: float = 0.007,
        maks_yuk_kapasitesi_kg: int = 26000,
        notlar: str = "",
    ) -> Arac:
        """
        Yeni araç ekle (TOCTOU Korumalı).
        Race condition önlemek için SELECT FOR UPDATE kullanılır.
        """
        session = self.session
        logger.debug(f"[AracRepository.add] Using session {id(session)}")
        # 1. Kayıt var mı kontrol et ve kilitle (TOCTOU Prevention)
        stmt = select(self.model).where(self.model.plaka == plaka).with_for_update()
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            logger.warning(f"TOCTOU Alert: Araç zaten mevcut ({plaka})")
            raise ValueError(f"Bu plaka ile araç zaten kayıtlı: {plaka}")

        # 2. Kaydı oluştur (ORM implementation for visibility)
        new_arac = self.model(
            plaka=plaka,
            marka=marka,
            model=model,
            yil=yil,
            tank_kapasitesi=tank_kapasitesi,
            hedef_tuketim=hedef_tuketim,
            bos_agirlik_kg=bos_agirlik_kg,
            hava_direnc_katsayisi=hava_direnc_katsayisi,
            on_kesit_alani_m2=on_kesit_alani_m2,
            motor_verimliligi=motor_verimliligi,
            lastik_direnc_katsayisi=lastik_direnc_katsayisi,
            maks_yuk_kapasitesi_kg=maks_yuk_kapasitesi_kg,
            notlar=notlar,
            aktif=True,
        )
        session.add(new_arac)
        await session.flush()
        return new_arac

    async def get_arac_with_stats(self, arac_id: int) -> Optional[Dict[str, Any]]:
        """Araç bilgisi + istatistikler"""
        query = """
            SELECT 
                a.id as arac_id,
                a.plaka,
                a.marka,
                a.model,
                a.yil,
                a.aktif,
                COUNT(s.id) as toplam_sefer,
                COALESCE(SUM(s.mesafe_km), 0) as toplam_km,
                COALESCE(SUM(s.tuketim), 0) as toplam_yakit,
                COALESCE(AVG(s.tuketim), 0.0) as ort_tuketim
            FROM araclar a
            LEFT JOIN seferler s ON a.id = s.arac_id AND s.tuketim IS NOT NULL
            WHERE a.id = :arac_id
            GROUP BY a.id, a.plaka, a.marka, a.model, a.yil, a.aktif
        """
        rows = await self.execute_query(query, {"arac_id": arac_id})
        return rows[0] if rows else None

    async def get_aktif_plakalar(self) -> List[str]:
        """Aktif araç plakalarını getir"""
        query = "SELECT plaka FROM araclar WHERE aktif = true ORDER BY plaka"
        rows = await self.execute_query(query)
        return [str(row["plaka"]) for row in rows]

    async def get_maintenance_candidates(self) -> Dict[str, Any]:
        """
        Bakım ihtiyacı olan araçları getir (Rule-based).
        Kriterler:
        1. Yaş > 15 (Eski araçlar)
        2. Ort. Tüketim > 35L (Yüksek tüketim)
        """
        query = """
            SELECT 
                a.id, a.plaka, a.marka, a.model, a.yil,
                COALESCE(AVG(s.tuketim), 0.0) as ort_tuketim
            FROM araclar a
            LEFT JOIN seferler s ON a.id = s.arac_id
            WHERE a.aktif = true
            GROUP BY a.id, a.plaka, a.marka, a.model, a.yil
            HAVING (2024 - a.yil) > 15 OR AVG(s.tuketim) > 35
            ORDER BY ort_tuketim DESC
            LIMIT 5
        """
        rows = await self.execute_query(query)

        candidates = []
        for row in rows:
            reason = []
            age = 2024 - row["yil"]
            if age > 15:
                reason.append(f"Yaşlı Araç ({age} yaşında)")
            if row["ort_tuketim"] > 35:
                reason.append(f"Yüksek Tüketim ({row['ort_tuketim']:.1f} L)")

            candidates.append(
                {
                    "id": row["id"],
                    "plaka": row["plaka"],
                    "reason": ", ".join(reason),
                    "severity": "high" if len(reason) > 1 else "medium",
                }
            )

        urgent_count = sum(1 for c in candidates if c["severity"] == "high")

        return {
            "urgent_count": urgent_count,
            "warning_count": len(candidates) - urgent_count,
            "vehicles": candidates,
        }

    async def hard_delete_all(self) -> int:
        """Tüm araçları tamamen sil (Tehlikeli!)"""
        session = self.session
        try:
            stmt = delete(self.model)
            result = await session.execute(stmt)
            await session.flush()
            return int(result.rowcount)
        except Exception as e:
            logger.error(f"Bulk delete error for vehicles: {e}")
            raise e


_arac_repo_lock = threading.Lock()
_arac_repo: Optional[AracRepository] = None


def get_arac_repo(session: Optional[AsyncSession] = None) -> AracRepository:
    """AracRepo Provider. Eğer session verilirse yeni instance döner (UoW için)."""
    global _arac_repo
    if session:
        return AracRepository(session=session)
    with _arac_repo_lock:
        if _arac_repo is None:
            _arac_repo = AracRepository()
    return _arac_repo
