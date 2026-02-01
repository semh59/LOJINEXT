"""
TIR Yakıt Takip - Sefer Repository
Sefer CRUD operasyonları
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.database.models import Sefer
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SeferRepository(BaseRepository[Sefer]):
    """Sefer veritabanı operasyonları (Async)"""

    model = Sefer

    async def get_all(
        self,
        tarih: str = None,
        baslangic_tarih: str = None,
        bitis_tarih: str = None,
        arac_id: int = None,
        sofor_id: int = None,
        durum: str = None,
        search: str = None,
        limit: int = 100,
        offset: int = 0,
        desc: bool = True,
        include_inactive: bool = False
    ) -> List[Dict]:
        """Seferleri getir (join ile plaka ve şoför adı dahil)"""
        # Input validation
        limit = max(1, min(int(limit or 100), self.MAX_LIMIT))
        offset = max(0, int(offset or 0))
        
        query = """
            SELECT s.*, a.plaka, sf.ad_soyad as sofor_adi
            FROM seferler s
            JOIN araclar a ON s.arac_id = a.id
            JOIN soforler sf ON s.sofor_id = sf.id
            WHERE 1=1
        """
        params = {}

        if tarih:
            query += " AND s.tarih = :tarih"
            params["tarih"] = date.fromisoformat(tarih) if isinstance(tarih, str) else tarih

        if baslangic_tarih:
            query += " AND s.tarih >= :baslangic_tarih"
            params["baslangic_tarih"] = date.fromisoformat(baslangic_tarih) if isinstance(baslangic_tarih, str) else baslangic_tarih

        if bitis_tarih:
            query += " AND s.tarih <= :bitis_tarih"
            params["bitis_tarih"] = date.fromisoformat(bitis_tarih) if isinstance(bitis_tarih, str) else bitis_tarih

        if arac_id:
            query += " AND s.arac_id = :arac_id"
            params["arac_id"] = arac_id

        if sofor_id:
            query += " AND s.sofor_id = :sofor_id"
            params["sofor_id"] = sofor_id

        if durum:
            query += " AND s.durum = :durum"
            params["durum"] = durum

        if search:
            query += """ AND (
                a.plaka LIKE :search OR 
                sf.ad_soyad LIKE :search OR 
                s.cikis_yeri LIKE :search OR 
                s.varis_yeri LIKE :search
            )"""
            params["search"] = f"%{search}%"
            
        # if not include_inactive:
        #    query += " AND s.aktif = TRUE"

        # ORDER BY Whitelist
        order_direction = "DESC" if desc else "ASC"
        
        # SQL Injection Prevention for dynamic ORDER BY
        query += f" ORDER BY s.tarih {order_direction}, s.id {order_direction} LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        return await self.execute_query(query, params)

    async def add(
        self,
        tarih: str,
        arac_id: int,
        sofor_id: int,
        mesafe_km: int,
        net_kg: int,
        cikis_yeri: str,
        varis_yeri: str,
        saat: str = "",
        bos_sefer: bool = False,
        ascent_m: float = None,
        descent_m: float = None,
        durum: str = 'Bekliyor',
        notlar: str = None,
        guzergah_id: int = None,
        bos_agirlik_kg: int = 0,
        dolu_agirlik_kg: int = 0
    ) -> int:
        """Yeni sefer ekle"""
        if isinstance(tarih, str):
            tarih_obj = date.fromisoformat(tarih)
        else:
            tarih_obj = tarih

        return await self.create(
            tarih=tarih_obj,
            arac_id=arac_id,
            sofor_id=sofor_id,
            guzergah_id=guzergah_id,
            mesafe_km=mesafe_km,
            net_kg=net_kg,
            ton=round(net_kg / 1000, 2),
            bos_agirlik_kg=bos_agirlik_kg,
            dolu_agirlik_kg=dolu_agirlik_kg,
            cikis_yeri=cikis_yeri,
            varis_yeri=varis_yeri,
            saat=saat if saat else None,
            bos_sefer=bos_sefer,
            durum=durum,
            ascent_m=ascent_m,
            descent_m=descent_m,
            notlar=notlar
        )

    async def get_bugunun_seferleri(self) -> List[Dict]:
        """Bugünün seferlerini getir"""
        bugun = date.today().isoformat()
        return await self.get_all(tarih=bugun, limit=50)

    async def get_by_id_with_details(self, id: int) -> Optional[Dict]:
        """ID ile sefer getir (detaylı)"""
        query = """
            SELECT s.*, a.plaka, sf.ad_soyad as sofor_adi
            FROM seferler s
            JOIN araclar a ON s.arac_id = a.id
            JOIN soforler sf ON s.sofor_id = sf.id
            WHERE s.id = :id
        """
        rows = await self.execute_query(query, {"id": id})
        return rows[0] if rows else None

    async def update_sefer(self, id: int, **kwargs) -> bool:
        """Sefer güncelle"""
        allowed = ["tarih", "arac_id", "sofor_id", "mesafe_km", "net_kg",
                   "cikis_yeri", "varis_yeri", "saat", "bos_sefer",
                   "tuketim", "dagitilan_yakit", "periyot_id", "durum",
                   "ascent_m", "descent_m", "notlar", "guzergah_id", 
                   "bos_agirlik_kg", "dolu_agirlik_kg"]

        if "net_kg" in kwargs:
             kwargs["ton"] = round(kwargs["net_kg"] / 1000, 2)

        updates = {k: v for k, v in kwargs.items() if k in allowed or k == "ton"}
        return await self.update(id, **updates)

    async def delete_permanently(self, id: int) -> bool:
        """
        Sefer kaydını veritabanından tamamen siler (Hard Delete).
        """
        async with self._get_session() as session:
            try:
                # Önce kaydı bul
                obj = await session.get(self.model, id)
                if not obj:
                    return False
                
                await session.delete(obj)
                
                if not self.session:
                    await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error hard deleting sefer {id}: {e}")
                if not self.session:
                    await session.rollback()
                raise e

    async def update_trips_fuel_data(self, trips: List[Any]) -> int:
        """
        Seferlerin yakıt verilerini toplu güncelle (Bulk Update).
        SQLAlchemy `executemany` (bindparam) kullanarak tek transaction'da işler.
        """
        if not trips:
            return 0
            
        count = 0
        from sqlalchemy import text
        
        # Güncellenecek verileri hazırla
        update_data = []
        for trip in trips:
            if hasattr(trip, 'id') and hasattr(trip, 'tuketim'):
                update_data.append({
                    "periyot_id": getattr(trip, 'periyot_id', None),
                    "dagitilan_yakit": getattr(trip, 'dagitilan_yakit', None),
                    "tuketim": trip.tuketim,
                    "id": trip.id
                })
        
        if not update_data:
            return 0

        async with self._get_session() as session:
            try:
                # Bulk Update Query
                stmt = text("""
                    UPDATE seferler 
                    SET periyot_id = :periyot_id, 
                        dagitilan_yakit = :dagitilan_yakit,
                        tuketim = :tuketim
                    WHERE id = :id
                """)
                
                # Tek seferde çalıştır
                result = await session.execute(stmt, update_data)
                count = result.rowcount
                
                if not self.session:
                    await session.commit()
                    
                logger.info(f"Updated {len(update_data)} trips with fuel data (Bulk)")
                    
            except Exception as e:
                logger.error(f"Bulk update failed: {e}")
                if not self.session:
                    await session.rollback()
                raise e

        return count

    async def get_for_training(
        self,
        arac_id: int,
        limit: int = 200
    ) -> List[Dict]:
        """
        AI model eğitimi için sefer verilerini getir.
        Sadece tüketim verisi olan ve tamamlanmış seferler.
        """
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


# Thread-safe Singleton
import threading
_sefer_repo_lock = threading.Lock()
_sefer_repo: Optional[SeferRepository] = None

def get_sefer_repo(session: Optional[AsyncSession] = None) -> SeferRepository:
    """SeferRepo Provider. Eğer session verilirse yeni instance döner (UoW için)."""
    global _sefer_repo
    if session:
        return SeferRepository(session=session)
    with _sefer_repo_lock:
        if _sefer_repo is None:
            _sefer_repo = SeferRepository()
    return _sefer_repo
