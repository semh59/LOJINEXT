"""
TIR Yakıt Takip - Araç Repository
Araç CRUD operasyonları
"""

from typing import Dict, List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

import app.database.connection as db_conn
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
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Tüm araçları getir (Arama ve Sayfalama destekli).
        """
        _filters = filters.copy() if filters else {}
        if search:
            _filters["search"] = search

        return await super().get_all(
            filters=_filters,
            order_by="plaka",
            limit=limit,
            offset=offset,
            include_inactive=not sadece_aktif
        )

    async def get_by_plaka(self, plaka: str) -> Optional[Dict]:
        """Plaka ile araç getir"""
        async with self._get_session() as session:
             stmt = select(self.model).where(self.model.plaka == plaka)
             result = await session.execute(stmt)
             obj = result.scalar_one_or_none()
             return self._to_dict(obj)

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
        notlar: str = ""
    ) -> int:
        """
        Yeni araç ekle (TOCTOU Korumalı).
        Race condition önlemek için SELECT FOR UPDATE kullanılır.
        """
        async with self._get_session() as session:
            # 1. Kayıt var mı kontrol et ve kilitle (TOCTOU Prevention)
            stmt = select(self.model).where(self.model.plaka == plaka).with_for_update()
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.warning(f"TOCTOU Alert: Araç zaten mevcut ({plaka})")
                raise ValueError(f"Bu plaka ile araç zaten kayıtlı: {plaka}")

            # 2. Kaydı oluştur
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
                aktif=True
            )
            session.add(new_arac)
            
            if not self.session:
                await session.commit()
                await session.refresh(new_arac)
            else:
                await session.flush()
            
            return new_arac.id

    async def get_arac_with_stats(self, arac_id: int) -> Optional[Dict]:
        """Araç bilgisi + istatistikler"""
        query = """
            SELECT 
                a.id as arac_id,
                a.plaka,
                COUNT(s.id) as toplam_sefer,
                COALESCE(SUM(s.mesafe_km), 0) as toplam_km,
                COALESCE(SUM(s.tuketim), 0) as toplam_yakit,
                COALESCE(AVG(s.tuketim), 0.0) as ort_tuketim
            FROM araclar a
            LEFT JOIN seferler s ON a.id = s.arac_id AND s.tuketim IS NOT NULL
            WHERE a.id = :arac_id
            GROUP BY a.id
        """
        rows = await self.execute_query(query, {"arac_id": arac_id})
        return rows[0] if rows else None

    async def get_aktif_plakalar(self) -> List[str]:
        """Aktif araç plakalarını getir"""
        query = "SELECT plaka FROM araclar WHERE aktif = true ORDER BY plaka"
        rows = await self.execute_query(query)
        return [row['plaka'] for row in rows]

    async def hard_delete_all(self) -> int:
        """Tüm araçları tamamen sil (Tehlikeli!)"""
        async with self._get_session() as session:
            try:
                stmt = delete(self.model)
                result = await session.execute(stmt)
                if not self.session:
                    await session.commit()
                return result.rowcount
            except Exception as e:
                if not self.session:
                    await session.rollback()
                logger.error(f"Bulk delete error for vehicles: {e}")
                raise e


# Thread-safe Singleton
import threading
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
