"""
TIR Yakıt Takip - Yakıt Repository
Yakıt alımı CRUD + periyot yönetimi
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import insert
from app.database.base_repository import BaseRepository
from app.database.models import YakitAlimi, YakitPeriyodu
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class YakitRepository(BaseRepository[YakitAlimi]):
    """Yakıt alımı veritabanı operasyonları (Async)"""

    model = YakitAlimi

    async def get_all(
        self,
        arac_id: int = None,
        limit: int = 100,
        offset: int = 0,
        desc: bool = True
    ) -> List[Dict]:
        """Yakıt alımlarını getir"""
        # Input validation
        limit = max(1, min(int(limit or 100), self.MAX_LIMIT))
        offset = max(0, int(offset or 0))

        query = """
            SELECT ya.*, a.plaka 
            FROM yakit_alimlari ya
            JOIN araclar a ON ya.arac_id = a.id
        """
        params = {}

        if arac_id:
            query += " WHERE ya.arac_id = :arac_id"
            params["arac_id"] = arac_id

        # ORDER BY Whitelist
        order_direction = "DESC" if desc else "ASC"
        
        # SQL Injection Prevention for dynamic ORDER BY
        query += f" ORDER BY ya.tarih {order_direction}, ya.km_sayac {order_direction} LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        return await self.execute_query(query, params)

    async def add(
        self,
        tarih: str,
        arac_id: int,
        istasyon: str,
        fiyat: float,
        litre: float,
        km_sayac: int,
        fis_no: str = "",
        depo_durumu: str = "Bilinmiyor",
        **kwargs
    ) -> int:
        """Yeni yakıt alımı ekle"""
        toplam = round(fiyat * litre, 2)

        if isinstance(tarih, str):
            tarih_obj = date.fromisoformat(tarih)
        else:
            tarih_obj = tarih

        return await self.create(
            tarih=tarih_obj,
            arac_id=arac_id,
            istasyon=istasyon,
            fiyat_tl=fiyat,
            litre=litre,
            toplam_tutar=toplam,
            km_sayac=km_sayac,
            fis_no=fis_no,
            depo_durumu=depo_durumu,
            durum='Bekliyor',
            **kwargs
        )

    async def get_son_km(self, arac_id: int) -> Optional[int]:
        """Aracın son KM değerini getir"""
        query = """
            SELECT MAX(km_sayac) as son_km 
            FROM yakit_alimlari 
            WHERE arac_id = :arac_id
        """
        result = await self.execute_scalar(query, {"arac_id": arac_id})
        return result

    async def update_yakit(self, id: int, **kwargs) -> bool:
        """Yakıt alımı güncelle"""
        allowed = ["tarih", "arac_id", "istasyon", "fiyat_tl", "litre",
                   "km_sayac", "fis_no", "depo_durumu", "durum"]

        updates = {k: v for k, v in kwargs.items() if k in allowed}

        # Toplam tutarı yeniden hesapla
        if "fiyat_tl" in updates and "litre" in updates:
            updates["toplam_tutar"] = round(updates["fiyat_tl"] * updates["litre"], 2)

        return await self.update(id, **updates)

    # =========================================================================
    # YAKIT PERİYOTLARI
    # =========================================================================

    async def save_fuel_periods(
        self,
        periods: List[Any],
        clear_existing: bool = False
    ) -> int:
        """
        Yakıt periyotlarını toplu kaydet (Async).
        """
        if not periods:
            return 0

        from sqlalchemy import text

        async with self._get_session() as session:
            try:
                if clear_existing:
                    arac_ids = set(p.arac_id for p in periods)
                    for arac_id in arac_ids:
                        await session.execute(
                            text("DELETE FROM yakit_periyotlari WHERE arac_id = :arac_id"),
                            {"arac_id": arac_id}
                        )

                count = 0
                # Bulk Insert Data Preparation
                insert_data = []
                for p in periods:
                    insert_data.append({
                        "arac_id": p.arac_id,
                        "alim1_id": p.alim1_id,
                        "alim2_id": p.alim2_id,
                        "alim1_tarih": p.alim1_tarih,
                        "alim2_tarih": p.alim2_tarih,
                        "alim1_km": p.alim1_km,
                        "alim2_km": p.alim2_km,
                        "alim1_litre": p.alim1_litre,
                        "ara_mesafe": p.ara_mesafe,
                        "toplam_yakit": p.toplam_yakit,
                        "ort_tuketim": p.ort_tuketim,
                        "durum": p.durum
                    })

                # Core Insert
                stmt = insert(YakitPeriyodu).values(insert_data)
                
                # Execute Bulk Insert
                result = await session.execute(stmt)
                count = len(insert_data)
                
                if not self.session:
                    await session.commit()

                logger.info(f"Saved {count} fuel periods (Bulk)")
                return count
            except Exception as e:
                if not self.session:
                    await session.rollback()
                raise e

    async def get_fuel_periods(self, arac_id: int, limit: int = 20) -> List[Dict]:
        """Aracın yakıt periyotlarını getir"""
        query = """
            SELECT * FROM yakit_periyotlari 
            WHERE arac_id = :arac_id
            ORDER BY alim2_tarih DESC
            LIMIT :limit
        """
        return await self.execute_query(query, {"arac_id": arac_id, "limit": limit})


# Thread-safe Singleton
import threading
from sqlalchemy.ext.asyncio import AsyncSession

_yakit_repo_lock = threading.Lock()
_yakit_repo: Optional[YakitRepository] = None

def get_yakit_repo(session: Optional[AsyncSession] = None) -> YakitRepository:
    """YakitRepo Provider. Eğer session verilirse yeni instance döner (UoW için)."""
    global _yakit_repo
    if session:
        return YakitRepository(session=session)
    with _yakit_repo_lock:
        if _yakit_repo is None:
            _yakit_repo = YakitRepository()
    return _yakit_repo
