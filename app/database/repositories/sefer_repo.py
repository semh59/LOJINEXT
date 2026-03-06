import threading
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from sqlalchemy import select, or_, desc as sql_desc, asc as sql_asc
from sqlalchemy.orm import joinedload
from app.database.models import Sefer, Arac, Sofor
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SeferRepository(BaseRepository[Sefer]):
    """Sefer veritabanı operasyonları (Async)"""

    model = Sefer

    async def get_all(
        self,
        tarih: Optional[date] = None,
        baslangic_tarih: Optional[date] = None,
        bitis_tarih: Optional[date] = None,
        arac_id: Optional[int] = None,
        sofor_id: Optional[int] = None,
        durum: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        desc: bool = True,
        include_inactive: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Seferleri getir (join ile plaka ve şoför adı dahil)"""
        # Dictionary formatındaki filtreleri üst seviye argümanlara eşitle (Service Layer uyumu)
        if filters:
            tarih = filters.get("tarih", tarih)
            baslangic_tarih = filters.get("baslangic_tarih", baslangic_tarih)
            bitis_tarih = filters.get("bitis_tarih", bitis_tarih)
            arac_id = filters.get("arac_id", arac_id)
            sofor_id = filters.get("sofor_id", sofor_id)
            durum = filters.get("durum", durum)
            search = filters.get("search", search)
            include_inactive = filters.get("include_inactive", include_inactive)

        # Date string conversion if needed
        if isinstance(tarih, str):
            tarih = date.fromisoformat(tarih)
        if isinstance(baslangic_tarih, str):
            baslangic_tarih = date.fromisoformat(baslangic_tarih)
        if isinstance(bitis_tarih, str):
            bitis_tarih = date.fromisoformat(bitis_tarih)

        # ID conversion if needed (sometimes passed as strings from query params)
        if arac_id is not None:
            arac_id = int(arac_id)
        if sofor_id is not None:
            sofor_id = int(sofor_id)

        # Input validation
        limit = max(1, min(int(limit or 100), self.MAX_LIMIT))
        offset = max(0, int(offset or 0))

        stmt = (
            select(Sefer)
            .options(
                joinedload(Sefer.arac),
                joinedload(Sefer.sofor),
                joinedload(Sefer.dorse),
                joinedload(Sefer.guzergah),
            )
            .where(Sefer.is_deleted.is_(False))
        )

        if tarih:
            stmt = stmt.where(Sefer.tarih == tarih)

        if baslangic_tarih:
            stmt = stmt.where(Sefer.tarih >= baslangic_tarih)

        if bitis_tarih:
            stmt = stmt.where(Sefer.tarih <= bitis_tarih)

        if arac_id:
            stmt = stmt.where(Sefer.arac_id == arac_id)

        if sofor_id:
            stmt = stmt.where(Sefer.sofor_id == sofor_id)

        if durum:
            stmt = stmt.where(Sefer.durum == durum)
        elif not include_inactive:
            # Varsayılan olarak İptal edilmiş seferleri gösterme
            stmt = stmt.where(Sefer.durum != "İptal")

        # Data Guarding: Real vs Synthetic
        is_real = filters.get("is_real") if filters else kwargs.get("is_real")
        if is_real is not None:
            stmt = stmt.where(Sefer.is_real == bool(is_real))

        if search:
            # For searching inside relationships, we can use an outerjoin directly into the query
            stmt = stmt.outerjoin(Arac, Sefer.arac_id == Arac.id).outerjoin(
                Sofor, Sefer.sofor_id == Sofor.id
            )
            stmt = stmt.where(
                or_(
                    Arac.plaka.ilike(f"%{search}%"),
                    Sofor.ad_soyad.ilike(f"%{search}%"),
                    Sefer.cikis_yeri.ilike(f"%{search}%"),
                    Sefer.varis_yeri.ilike(f"%{search}%"),
                    Sefer.sefer_no.ilike(f"%{search}%"),
                )
            )

        # ORDER BY
        if desc:
            stmt = stmt.order_by(sql_desc(Sefer.tarih), sql_desc(Sefer.id))
        else:
            stmt = stmt.order_by(sql_asc(Sefer.tarih), sql_asc(Sefer.id))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        seferler = result.scalars().unique().all()

        data = []
        for s in seferler:
            d = s.__dict__.copy()
            d.pop("_sa_instance_state", None)
            d["plaka"] = s.arac.plaka if s.arac else None
            d["sofor_adi"] = s.sofor.ad_soyad if s.sofor else None
            d["dorse_plakasi"] = s.dorse.plaka if s.dorse else None
            if s.guzergah:
                d["guzergah_adi"] = f"{s.guzergah.cikis_yeri} - {s.guzergah.varis_yeri}"
            else:
                d["guzergah_adi"] = f"{s.cikis_yeri} - {s.varis_yeri}"
            data.append(d)

        return data

    async def get_cost_leakage_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Son X gündeki maliyet kaçaklarını hesapla (Rota Sapması ve Yakıt Farkı).
        """
        start_date = date.today() - timedelta(days=days)
        from sqlalchemy import text

        # 1. Rota Sapması Maliyeti (Gerçekleşen > Hedef)
        # Varsayım: 1 km sapma = O anki yakıt fiyatı * ortalama tüketim (örn: 32L/100km)
        # Basitleştirilmiş: 40 TL/L * 0.32 L/km = ~12.8 TL/km
        route_query = """
            SELECT 
                SUM(s.mesafe_km - l.mesafe_km) as total_deviation_km
            FROM seferler s
            JOIN lokasyonlar l ON s.guzergah_id = l.id
            WHERE s.tarih >= :start_date 
            AND s.mesafe_km > l.mesafe_km
            AND s.durum = 'Tamam'
        """

        # 2. Yakıt Farkı Maliyeti (Gerçekleşen > Hedef/Beklenen)
        # Tüketim (Litre) farkı
        fuel_query = """
            SELECT 
                SUM(s.tuketim - (s.mesafe_km * a.hedef_tuketim / 100)) as total_fuel_gap_liters
            FROM seferler s
            JOIN araclar a ON s.arac_id = a.id
            WHERE s.tarih >= :start_date
            AND s.tuketim > (s.mesafe_km * a.hedef_tuketim / 100)
            AND s.durum = 'Tamam'
        """

        session = self.session
        route_result = await session.execute(
            text(route_query), {"start_date": start_date}
        )
        fuel_result = await session.execute(
            text(fuel_query), {"start_date": start_date}
        )

        dev_km = route_result.scalar() or 0
        fuel_gap = fuel_result.scalar() or 0

        # Ortalama Yakıt Fiyatı (Hızlı hesap için sabit veya son alımdan alınabilir)
        AVG_FUEL_PRICE = 42.0  # TL (Dinamik yapılabilir)
        EST_KM_COST = 13.5  # TL/km (yakıt + amortisman)

        return {
            "route_deviation_km": round(float(dev_km), 1),
            "route_deviation_cost": round(float(dev_km) * EST_KM_COST, 2),
            "fuel_gap_liters": round(float(fuel_gap), 1),
            "fuel_gap_cost": round(float(fuel_gap) * AVG_FUEL_PRICE, 2),
            "total_leakage_cost": round(
                (float(dev_km) * EST_KM_COST) + (float(fuel_gap) * AVG_FUEL_PRICE),
                2,
            ),
        }

    async def count_all(
        self,
        tarih: Optional[date] = None,
        baslangic_tarih: Optional[date] = None,
        bitis_tarih: Optional[date] = None,
        arac_id: Optional[int] = None,
        sofor_id: Optional[int] = None,
        durum: Optional[str] = None,
        search: Optional[str] = None,
        include_inactive: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> int:
        """Filtrelere uyan toplam sefer sayısını getir"""
        if filters:
            tarih = filters.get("tarih", tarih)
            baslangic_tarih = filters.get("baslangic_tarih", baslangic_tarih)
            bitis_tarih = filters.get("bitis_tarih", bitis_tarih)
            arac_id = filters.get("arac_id", arac_id)
            sofor_id = filters.get("sofor_id", sofor_id)
            durum = filters.get("durum", durum)
            search = filters.get("search", search)
            include_inactive = filters.get("include_inactive", include_inactive)

        # Date string conversion if needed
        if isinstance(tarih, str):
            tarih = date.fromisoformat(tarih)
        if isinstance(baslangic_tarih, str):
            baslangic_tarih = date.fromisoformat(baslangic_tarih)
        if isinstance(bitis_tarih, str):
            bitis_tarih = date.fromisoformat(bitis_tarih)

        # ID conversion if needed
        if arac_id is not None:
            arac_id = int(arac_id)
        if sofor_id is not None:
            sofor_id = int(sofor_id)

        query = """
            SELECT COUNT(*)
            FROM seferler s
            JOIN araclar a ON s.arac_id = a.id
            JOIN soforler sf ON s.sofor_id = sf.id
            WHERE 1=1 AND s.is_deleted = False
        """
        params: Dict[str, Any] = {}

        if tarih:
            query += " AND s.tarih = :tarih"
            params["tarih"] = tarih

        if baslangic_tarih:
            query += " AND s.tarih >= :baslangic_tarih"
            params["baslangic_tarih"] = baslangic_tarih

        if bitis_tarih:
            query += " AND s.tarih <= :bitis_tarih"
            params["bitis_tarih"] = bitis_tarih

        if arac_id:
            query += " AND s.arac_id = :arac_id"
            params["arac_id"] = arac_id

        if sofor_id:
            query += " AND s.sofor_id = :sofor_id"
            params["sofor_id"] = sofor_id

        if durum:
            query += " AND s.durum = :durum"
            params["durum"] = durum
        elif not include_inactive:
            query += " AND s.durum != 'İptal'"

        # Data Guarding: Real vs Synthetic
        is_real = filters.get("is_real") if filters else kwargs.get("is_real")
        if is_real is not None:
            query += " AND s.is_real = :is_real"
            params["is_real"] = bool(is_real)

        if search:
            query += """ AND (
                a.plaka LIKE :search OR 
                sf.ad_soyad LIKE :search OR 
                s.cikis_yeri LIKE :search OR 
                s.varis_yeri LIKE :search OR
                s.sefer_no LIKE :search
            )"""
            params["search"] = f"%{search}%"

        return await self.execute_scalar(query, params) or 0

    async def has_active_trip(
        self, arac_id: int, exclude_sefer_id: Optional[int] = None
    ) -> bool:
        """Aracın halihazırda 'Devam Ediyor' veya 'Yolda' olan bir seferi var mı?"""
        query = """
            SELECT EXISTS(
                SELECT 1 FROM seferler 
                WHERE arac_id = :arac_id 
                AND is_deleted = False
                AND durum IN ('Devam Ediyor', 'Yolda')
        """
        params = {"arac_id": arac_id}
        if exclude_sefer_id:
            query += " AND id != :exclude_id"
            params["exclude_id"] = exclude_sefer_id

        query += ")"
        return bool(await self.execute_scalar(query, params))

    async def get_by_sefer_no(self, sefer_no: str) -> Optional[Dict[str, Any]]:
        """Sefer numarasına göre sefer getir (join dahil)"""
        stmt = (
            select(Sefer)
            .options(
                joinedload(Sefer.arac),
                joinedload(Sefer.sofor),
                joinedload(Sefer.dorse),
                joinedload(Sefer.guzergah),
            )
            .where(Sefer.sefer_no == sefer_no, Sefer.is_deleted.is_(False))
        )

        result = await self.session.execute(stmt)
        s = result.scalars().first()

        if not s:
            return None

        d = s.__dict__.copy()
        d.pop("_sa_instance_state", None)
        d["plaka"] = s.arac.plaka if s.arac else None
        d["sofor_adi"] = s.sofor.ad_soyad if s.sofor else None
        d["dorse_plakasi"] = s.dorse.plaka if s.dorse else None
        if s.guzergah:
            d["guzergah_adi"] = f"{s.guzergah.cikis_yeri} - {s.guzergah.varis_yeri}"
        else:
            d["guzergah_adi"] = f"{s.cikis_yeri} - {s.varis_yeri}"
        return d

    async def add(
        self,
        tarih: date,
        arac_id: int,
        sofor_id: int,
        mesafe_km: float,
        net_kg: int,
        cikis_yeri: str,
        varis_yeri: str,
        dorse_id: Optional[int] = None,
        sefer_no: Optional[str] = None,
        saat: Optional[str] = None,
        bos_sefer: bool = False,
        ascent_m: Optional[float] = None,
        descent_m: Optional[float] = None,
        durum: str = "Bekliyor",
        notlar: Optional[str] = None,
        guzergah_id: Optional[int] = None,
        bos_agirlik_kg: int = 0,
        dolu_agirlik_kg: int = 0,
        flat_distance_km: float = 0.0,
        tahmini_tuketim: Optional[float] = None,
        is_real: bool = True,
        rota_detay: Optional[Dict] = None,
        otoban_mesafe_km: Optional[float] = None,
        sehir_ici_mesafe_km: Optional[float] = None,
        created_by_id: Optional[int] = None,
        updated_by_id: Optional[int] = None,
        iptal_nedeni: Optional[str] = None,
    ) -> int:
        """Yeni sefer ekle"""
        return await self.create(
            tarih=tarih,
            arac_id=arac_id,
            dorse_id=dorse_id,
            sofor_id=sofor_id,
            guzergah_id=guzergah_id,
            mesafe_km=mesafe_km,
            net_kg=net_kg,
            sefer_no=sefer_no,
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
            flat_distance_km=flat_distance_km,
            tahmini_tuketim=tahmini_tuketim,
            is_real=is_real,
            notlar=notlar,
            rota_detay=rota_detay,
            otoban_mesafe_km=otoban_mesafe_km,
            sehir_ici_mesafe_km=sehir_ici_mesafe_km,
            created_by_id=created_by_id,
            updated_by_id=updated_by_id,
            iptal_nedeni=iptal_nedeni,
        )

    async def get_bugunun_seferleri(self) -> List[Dict[str, Any]]:
        """Bugünün seferlerini getir"""
        return await self.get_all(tarih=date.today(), limit=50)

    async def get_by_id(
        self, id: int, current_user: Optional[Any] = None, for_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        """ID ile sefer getir (join ile plaka ve şoför adı dahil)"""
        # Session handling for update
        if for_update:
            return await super().get_by_id(id, for_update=True)

        stmt = (
            select(Sefer)
            .options(
                joinedload(Sefer.arac),
                joinedload(Sefer.sofor),
                joinedload(Sefer.dorse),
                joinedload(Sefer.guzergah),
            )
            .where(Sefer.id == id, Sefer.is_deleted.is_(False))
        )

        result = await self.session.execute(stmt)
        s = result.scalars().first()

        if not s:
            return None

        d = s.__dict__.copy()
        d.pop("_sa_instance_state", None)
        d["plaka"] = s.arac.plaka if s.arac else None
        d["sofor_adi"] = s.sofor.ad_soyad if s.sofor else None
        d["dorse_plakasi"] = s.dorse.plaka if s.dorse else None
        if s.guzergah:
            d["guzergah_adi"] = f"{s.guzergah.cikis_yeri} - {s.guzergah.varis_yeri}"
        else:
            d["guzergah_adi"] = f"{s.cikis_yeri} - {s.varis_yeri}"
        return d

    async def get_by_id_with_details(self, id: int) -> Optional[Dict[str, Any]]:
        """ID ile sefer getir (detaylı)"""
        return await self.get_by_id(id)

    async def update_sefer(self, id: int, **kwargs: Any) -> bool:
        """Sefer güncelle"""
        allowed = [
            "tarih",
            "arac_id",
            "sofor_id",
            "mesafe_km",
            "net_kg",
            "cikis_yeri",
            "varis_yeri",
            "saat",
            "bos_sefer",
            "tuketim",
            "dagitilan_yakit",
            "periyot_id",
            "durum",
            "ascent_m",
            "descent_m",
            "notlar",
            "guzergah_id",
            "dorse_id",
            "bos_agirlik_kg",
            "dolu_agirlik_kg",
            "flat_distance_km",
            "tahmini_tuketim",
            "sefer_no",
            "is_real",
            "rota_detay",
            "otoban_mesafe_km",
            "sehir_ici_mesafe_km",
            "created_by_id",
            "updated_by_id",
            "iptal_nedeni",
            "is_deleted",
        ]

        if "net_kg" in kwargs:
            kwargs["ton"] = round(kwargs["net_kg"] / 1000, 2)

        updates = {k: v for k, v in kwargs.items() if k in allowed or k == "ton"}
        return await self.update(id, **updates)

    async def delete_permanently(self, id: int) -> bool:
        """
        Sefer kaydını veritabanından tamamen siler (Hard Delete).
        """
        session = self.session
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

    async def delete(self, id: int) -> bool:
        """
        Soft delete implementation. Hard delete relies on `delete_permanently`.
        """
        return await self.update_sefer(
            id,
            is_deleted=True,
            durum="İptal",
            iptal_nedeni="Sistem tarafından silindi (Soft Delete)",
        )

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
            if hasattr(trip, "id") and hasattr(trip, "tuketim"):
                update_data.append(
                    {
                        "periyot_id": getattr(trip, "periyot_id", None),
                        "dagitilan_yakit": getattr(trip, "dagitilan_yakit", None),
                        "tuketim": trip.tuketim,
                        "id": trip.id,
                    }
                )

        if not update_data:
            return 0

        session = self.session
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

    async def get_suspicious_trips(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Şüpheli seferleri getir (Örn: Tamamlanmış ama tüketim girilmemiş).
        VerifierService tarafından kullanılır.
        """
        query = """
            SELECT s.id, s.tarih, a.plaka, s.durum, s.tuketim, s.sefer_no
            FROM seferler s
            JOIN araclar a ON s.arac_id = a.id
            WHERE s.durum = 'Tamam' 
              AND s.is_deleted = False
              AND (s.tuketim IS NULL OR s.tuketim = 0)
            ORDER BY s.tarih DESC
            LIMIT :limit
        """
        return await self.execute_query(query, {"limit": limit})

    async def get_for_training(
        self, arac_id: int, limit: int = 200, include_synthetic: bool = False
    ) -> List[Dict]:
        """
        AI model eğitimi için sefer verilerini getir.
        Sadece tüketim verisi olan ve tamamlanmış seferler.
        """
        is_real_filter = "AND s.is_real = TRUE" if not include_synthetic else ""
        query = f"""
            SELECT 
                s.mesafe_km,
                s.net_kg / 1000.0 as ton,
                s.tuketim,
                s.sofor_id,
                COALESCE(s.ascent_m, l.ascent_m, 0.0) as ascent_m,
                COALESCE(s.descent_m, l.descent_m, 0.0) as descent_m,
                COALESCE(s.flat_distance_km, l.flat_distance_km, 0.0) as flat_distance_km,
                COALESCE(l.zorluk, 'Normal') as zorluk,
                s.rota_detay
            FROM seferler s
            LEFT JOIN lokasyonlar l ON (
                LOWER(s.cikis_yeri) = LOWER(l.cikis_yeri) AND 
                LOWER(s.varis_yeri) = LOWER(l.varis_yeri)
            )
            WHERE s.arac_id = :arac_id 
              AND s.is_deleted = False
              AND s.tuketim IS NOT NULL 
              AND s.tuketim > 0
              AND s.durum = 'Tamam'
              {is_real_filter}
            ORDER BY s.tarih DESC
            LIMIT :limit
        """
        return await self.execute_query(query, {"arac_id": arac_id, "limit": limit})

    async def refresh_stats_mv(self) -> None:
        """Sefer istatistik materialized view'ı yenile (Async)."""
        try:
            # PostgreSQL specific: REFRESH MATERIALIZED VIEW
            # CONCURRENTLY requires a unique index on the view,
            # if fails, falls back to standard refresh.
            from sqlalchemy import text

            await self.session.execute(
                text("REFRESH MATERIALIZED VIEW CONCURRENTLY sefer_istatistik_mv")
            )
            logger.info("Sefer Stats MV refreshed concurrently.")
        except Exception as e:
            logger.warning(
                f"Concurrent refresh failed (likely missing index), trying standard: {e}"
            )
            try:
                await self.session.execute(
                    text("REFRESH MATERIALIZED VIEW sefer_istatistik_mv")
                )
                logger.info("Sefer Stats MV refreshed standard.")
            except Exception as e2:
                logger.error(f"Sefer Stats MV refresh failed completely: {e2}")


# Thread-safe Singleton
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
