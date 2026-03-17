from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from sqlalchemy import select, or_, desc as sql_desc, asc as sql_asc, func, text
from sqlalchemy.orm import joinedload
from app.database.models import Sefer, Arac, Sofor
from app.infrastructure.logging.logger import get_logger
from app.core.utils.sefer_status import (
    SEFER_STATUS_IPTAL,
    ensure_canonical_sefer_status,
)

logger = get_logger(__name__)


class SeferRepository(BaseRepository[Sefer]):
    """Sefer veritabani operasyonlari (Async)"""

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
        """Seferleri getir (join ile plaka ve sofor adi dahil)"""
        # Dictionary formatindaki filtreleri ust seviye argumanlara esitle (Service Layer uyumu)
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
            durum = ensure_canonical_sefer_status(
                durum, field_name="durum", allow_none=False
            )
            stmt = stmt.where(Sefer.durum == durum)
        elif not include_inactive:
            # Varsayilan olarak iptal edilmis seferleri gosterme
            stmt = stmt.where(Sefer.durum != SEFER_STATUS_IPTAL)

        # Data Guarding: Real vs Synthetic
        is_real = filters.get("is_real") if filters else kwargs.get("is_real")
        if is_real is not None:
            stmt = stmt.where(Sefer.is_real == bool(is_real))

        if search:
            search_like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Sefer.arac.has(Arac.plaka.ilike(search_like)),
                    Sefer.sofor.has(Sofor.ad_soyad.ilike(search_like)),
                    Sefer.cikis_yeri.ilike(search_like),
                    Sefer.varis_yeri.ilike(search_like),
                    Sefer.sefer_no.ilike(search_like),
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
        Son X gundeki maliyet kacaklarini hesapla (Rota Sapmasi ve Yakit Farki).
        """
        start_date = date.today() - timedelta(days=days)

        # 1. Rota Sapmasi Maliyeti (Gerceklesen > Hedef)
        route_query = """
            SELECT 
                SUM(s.mesafe_km - l.mesafe_km) as total_deviation_km
            FROM seferler s
            JOIN lokasyonlar l ON s.guzergah_id = l.id
            WHERE s.tarih >= :start_date 
            AND s.mesafe_km > l.mesafe_km
            AND s.durum = 'Tamam'
        """

        # 2. Yakit Farki Maliyeti (Gerceklesen > Hedef/Beklenen)
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

        AVG_FUEL_PRICE = 42.0  # TL
        EST_KM_COST = 13.5  # TL/km

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
        """Filtrelere uyan toplam sefer sayisini getir"""
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
            durum = ensure_canonical_sefer_status(
                durum, field_name="durum", allow_none=False
            )
            query += " AND s.durum = :durum"
            params["durum"] = durum
        elif not include_inactive:
            query += " AND s.durum != :iptal_durum"
            params["iptal_durum"] = SEFER_STATUS_IPTAL

        # Data Guarding: Real vs Synthetic
        is_real = filters.get("is_real") if filters else kwargs.get("is_real")
        if is_real is not None:
            query += " AND s.is_real = :is_real"
            params["is_real"] = bool(is_real)

        if search:
            query += """ AND (
                a.plaka ILIKE :search OR 
                sf.ad_soyad ILIKE :search OR 
                s.cikis_yeri ILIKE :search OR 
                s.varis_yeri ILIKE :search OR
                s.sefer_no ILIKE :search
            )"""
            params["search"] = f"%{search}%"

        return await self.execute_scalar(query, params) or 0

    async def has_active_trip(
        self, arac_id: int, exclude_sefer_id: Optional[int] = None
    ) -> bool:
        """Aracin halihazirda 'Devam Ediyor' veya 'Yolda' olan bir seferi var mi?"""
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

    async def get_trip_stats(
        self,
        durum: Optional[str] = None,
        baslangic_tarih: Optional[date] = None,
        bitis_tarih: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Return trip statistics (dynamic query or materialized view)."""
        use_dynamic = bool(baslangic_tarih or bitis_tarih)
        if durum:
            durum = ensure_canonical_sefer_status(
                durum, field_name="durum", allow_none=False
            )

        if use_dynamic:
            stmt = select(
                func.count(Sefer.id).label("toplam_sefer"),
                func.sum(Sefer.mesafe_km).label("toplam_km"),
                func.sum(Sefer.otoban_mesafe_km).label("highway_km"),
                func.sum(Sefer.ascent_m).label("total_ascent"),
                func.sum(Sefer.net_kg / 1000.0).label("total_weight"),
                func.max(Sefer.created_at).label("last_updated"),
            ).where(
                Sefer.is_real.is_(True),
                Sefer.is_deleted.is_(False),
                Sefer.durum != SEFER_STATUS_IPTAL,
            )
            if durum:
                stmt = stmt.where(Sefer.durum == durum)
            if baslangic_tarih:
                stmt = stmt.where(Sefer.tarih >= baslangic_tarih)
            if bitis_tarih:
                stmt = stmt.where(Sefer.tarih <= bitis_tarih)
            result = await self.session.execute(stmt)
            row = result.mappings().first() or {}
        else:
            if durum:
                mv_query = text(
                    """
                    SELECT toplam_sefer, toplam_km, highway_km, total_ascent, total_weight, last_updated
                    FROM sefer_istatistik_mv
                    WHERE durum = :durum
                    """
                )
                result = await self.session.execute(mv_query, {"durum": durum})
                row = result.mappings().first() or {}
            else:
                mv_query = text(
                    """
                    SELECT
                        SUM(toplam_sefer) AS toplam_sefer,
                        SUM(toplam_km) AS toplam_km,
                        SUM(highway_km) AS highway_km,
                        SUM(total_ascent) AS total_ascent,
                        SUM(total_weight) AS total_weight,
                        MAX(last_updated) AS last_updated
                    FROM sefer_istatistik_mv
                    """
                )
                result = await self.session.execute(mv_query)
                row = result.mappings().first() or {}

        toplam_sefer = int(row.get("toplam_sefer") or 0)
        toplam_km = float(row.get("toplam_km") or 0.0)
        highway_km = float(row.get("highway_km") or 0.0)
        total_ascent = float(row.get("total_ascent") or 0.0)
        total_weight = float(row.get("total_weight") or 0.0)
        avg_highway_pct = (
            int(round((highway_km / toplam_km) * 100)) if toplam_km > 0 else 0
        )

        return {
            "toplam_sefer": toplam_sefer,
            "toplam_km": toplam_km,
            "highway_km": highway_km,
            "total_ascent": total_ascent,
            "total_weight": total_weight,
            "avg_highway_pct": avg_highway_pct,
            "last_updated": row.get("last_updated"),
        }

    async def get_by_sefer_no(self, sefer_no: str) -> Optional[Dict[str, Any]]:
        """Sefer numarasina gore sefer getir (join dahil)"""
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
        tahmin_meta: Optional[Dict] = None,
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
            tahmin_meta=tahmin_meta,
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
        """Bugunun seferlerini getir"""
        return await self.get_all(tarih=date.today(), limit=50)

    async def get_by_id(
        self, id: int, current_user: Optional[Any] = None, for_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        """ID ile sefer getir (join ile plaka ve sofor adi dahil)"""
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
        """ID ile sefer getir (detayli)"""
        return await self.get_by_id(id)

    async def update_sefer(self, id: int, **kwargs: Any) -> bool:
        """Sefer guncelle"""
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
            "tahmin_meta",
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
        Sefer kaydini veritabanindan tamamen siler (Hard Delete).
        """
        session = self.session
        try:
            # Once kaydi bul
            obj = await session.get(self.model, id)
            if not obj:
                return False

            await session.delete(obj)
            await session.flush()
            return True
        except Exception as e:
            logger.error(f"Error hard deleting sefer {id}: {e}")
            raise e

    async def delete(self, id: int) -> bool:
        """
        Soft delete implementation. Hard delete relies on `delete_permanently`.
        """
        return await self.update_sefer(
            id,
            is_deleted=True,
            durum=SEFER_STATUS_IPTAL,
            iptal_nedeni="Sistem tarafindan silindi (Soft Delete)",
        )

    async def update_trips_fuel_data(self, trips: List[Any]) -> int:
        """
        Seferlerin yakit verilerini toplu guncelle (Bulk Update).
        SQLAlchemy `executemany` (bindparam) kullanarak tek transaction'da isler.
        """
        if not trips:
            return 0

        count = 0

        # Guncellenecek verileri hazirla
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

            # Tek seferde calistir
            result = await session.execute(stmt, update_data)
            count = result.rowcount
            await session.flush()

            logger.info(f"Updated {len(update_data)} trips with fuel data (Bulk)")

        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            raise e

        return count

    async def get_suspicious_trips(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Supheli seferleri getir (Orn: Tamamlanmis ama tuketim girilmemis).
        VerifierService tarafindan kullanilir.
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
        AI model egitimi icin sefer verilerini getir.
        Sadece tuketim verisi olan ve tamamlanmis seferler.
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

    async def get_fuel_performance_analytics(
        self,
        durum: Optional[str] = None,
        baslangic_tarih: Optional[date] = None,
        bitis_tarih: Optional[date] = None,
        arac_id: Optional[int] = None,
        sofor_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tahmin performansini kullaniciya uygun KPI + trend + dagilim + outlier yapisinda getirir.
        """
        where_clauses = [
            "s.is_deleted = FALSE",
            "s.tahmini_tuketim IS NOT NULL",
            "s.tuketim IS NOT NULL",
            "s.tuketim > 0",
            "s.tahmini_tuketim > 0",
        ]
        params: Dict[str, Any] = {}

        if durum:
            where_clauses.append("s.durum = :durum")
            params["durum"] = durum
        if baslangic_tarih:
            where_clauses.append("s.tarih >= :baslangic_tarih")
            params["baslangic_tarih"] = baslangic_tarih
        if bitis_tarih:
            where_clauses.append("s.tarih <= :bitis_tarih")
            params["bitis_tarih"] = bitis_tarih
        if arac_id:
            where_clauses.append("s.arac_id = :arac_id")
            params["arac_id"] = arac_id
        if sofor_id:
            where_clauses.append("s.sofor_id = :sofor_id")
            params["sofor_id"] = sofor_id
        if search:
            where_clauses.append(
                """
                (
                    a.plaka ILIKE :search OR
                    sf.ad_soyad ILIKE :search OR
                    s.cikis_yeri ILIKE :search OR
                    s.varis_yeri ILIKE :search OR
                    s.sefer_no ILIKE :search
                )
                """
            )
            params["search"] = f"%{search}%"

        where_stmt = " AND ".join(where_clauses)

        summary_query = f"""
            SELECT
                COUNT(*) AS total_compared,
                AVG(ABS(s.tuketim - s.tahmini_tuketim)) AS mae,
                SQRT(AVG(POWER(s.tuketim - s.tahmini_tuketim, 2))) AS rmse,
                AVG(
                    CASE
                        WHEN ABS(s.tuketim - s.tahmini_tuketim) / NULLIF(s.tahmini_tuketim, 0) > 0.15
                        THEN 1.0
                        ELSE 0.0
                    END
                ) AS high_deviation_ratio
            FROM seferler s
            JOIN araclar a ON a.id = s.arac_id
            JOIN soforler sf ON sf.id = s.sofor_id
            WHERE {where_stmt}
        """

        trend_query = f"""
            SELECT
                s.tarih AS date,
                AVG(s.tahmini_tuketim) AS predicted,
                AVG(s.tuketim) AS actual
            FROM seferler s
            JOIN araclar a ON a.id = s.arac_id
            JOIN soforler sf ON sf.id = s.sofor_id
            WHERE {where_stmt}
            GROUP BY s.tarih
            ORDER BY s.tarih ASC
        """

        distribution_query = f"""
            SELECT
                SUM(
                    CASE
                        WHEN ABS(s.tuketim - s.tahmini_tuketim) / NULLIF(s.tahmini_tuketim, 0) <= 0.05 THEN 1
                        ELSE 0
                    END
                ) AS good,
                SUM(
                    CASE
                        WHEN ABS(s.tuketim - s.tahmini_tuketim) / NULLIF(s.tahmini_tuketim, 0) > 0.05
                             AND ABS(s.tuketim - s.tahmini_tuketim) / NULLIF(s.tahmini_tuketim, 0) <= 0.15
                        THEN 1
                        ELSE 0
                    END
                ) AS warning,
                SUM(
                    CASE
                        WHEN ABS(s.tuketim - s.tahmini_tuketim) / NULLIF(s.tahmini_tuketim, 0) > 0.15 THEN 1
                        ELSE 0
                    END
                ) AS error
            FROM seferler s
            JOIN araclar a ON a.id = s.arac_id
            JOIN soforler sf ON sf.id = s.sofor_id
            WHERE {where_stmt}
        """

        outlier_query = f"""
            SELECT
                s.id,
                s.sefer_no,
                s.tarih,
                a.plaka,
                sf.ad_soyad AS sofor_adi,
                s.tahmini_tuketim AS predicted,
                s.tuketim AS actual,
                ROUND(
                    (
                        ABS(s.tuketim - s.tahmini_tuketim) / NULLIF(s.tahmini_tuketim, 0)
                    )::numeric * 100,
                    2
                ) AS sapma_pct,
                CASE
                    WHEN s.bos_sefer THEN 'Bos sefer etkisi'
                    WHEN COALESCE(s.ascent_m, 0) > 800 THEN 'Yuksek tirmanis'
                    WHEN COALESCE(s.net_kg, 0) > 22000 THEN 'Yuksek yuk'
                    WHEN COALESCE(s.tahmin_meta->>'fallback_triggered', 'false') = 'true' THEN 'Model fallback'
                    ELSE 'Operasyonel fark'
                END AS reason_label
            FROM seferler s
            JOIN araclar a ON a.id = s.arac_id
            JOIN soforler sf ON sf.id = s.sofor_id
            WHERE {where_stmt}
            ORDER BY sapma_pct DESC
            LIMIT 10
        """

        summary_rows = await self.execute_query(summary_query, params)
        summary = summary_rows[0] if summary_rows else {}
        trend = await self.execute_query(trend_query, params)
        distribution_rows = await self.execute_query(distribution_query, params)
        distribution = distribution_rows[0] if distribution_rows else {}
        outliers = await self.execute_query(outlier_query, params)

        total_compared = int(summary.get("total_compared") or 0)
        good = int(distribution.get("good") or 0)
        warning = int(distribution.get("warning") or 0)
        error = int(distribution.get("error") or 0)
        safe_total = total_compared if total_compared > 0 else 1

        return {
            "kpis": {
                "mae": round(float(summary.get("mae") or 0.0), 2),
                "rmse": round(float(summary.get("rmse") or 0.0), 2),
                "total_compared": total_compared,
                "high_deviation_ratio": round(
                    float(summary.get("high_deviation_ratio") or 0.0) * 100, 2
                ),
            },
            "trend": [
                {
                    "date": row.get("date").isoformat()
                    if hasattr(row.get("date"), "isoformat")
                    else (
                        str(row.get("date")) if row.get("date") is not None else None
                    ),
                    "predicted": round(float(row.get("predicted") or 0.0), 2),
                    "actual": round(float(row.get("actual") or 0.0), 2),
                }
                for row in trend
            ],
            "distribution": {
                "good": good,
                "warning": warning,
                "error": error,
                "good_pct": round((good / safe_total) * 100, 2),
                "warning_pct": round((warning / safe_total) * 100, 2),
                "error_pct": round((error / safe_total) * 100, 2),
            },
            "outliers": [
                {
                    "id": row.get("id"),
                    "sefer_no": row.get("sefer_no"),
                    "tarih": row.get("tarih").isoformat()
                    if hasattr(row.get("tarih"), "isoformat")
                    else (
                        str(row.get("tarih")) if row.get("tarih") is not None else None
                    ),
                    "plaka": row.get("plaka"),
                    "sofor_adi": row.get("sofor_adi"),
                    "predicted": round(float(row.get("predicted") or 0.0), 2),
                    "actual": round(float(row.get("actual") or 0.0), 2),
                    "sapma_pct": round(float(row.get("sapma_pct") or 0.0), 2),
                    "reason_label": row.get("reason_label"),
                }
                for row in outliers
            ],
            "low_data": total_compared < 3,
        }

    async def refresh_stats_mv(self) -> None:
        """Sefer istatistik materialized view'i yenile (Async)."""
        try:
            # MV yoksa REFRESH denemesi yapilmasin.
            exists_result = await self.session.execute(
                text("SELECT to_regclass('public.sefer_istatistik_mv')")
            )
            if not exists_result.scalar():
                logger.debug("Sefer Stats MV not found; refresh skipped.")
                return

            # PostgreSQL specific: REFRESH MATERIALIZED VIEW
            # CONCURRENTLY requires a unique index on the view.
            await self.session.execute(
                text("REFRESH MATERIALIZED VIEW CONCURRENTLY sefer_istatistik_mv")
            )
            logger.info("Sefer Stats MV refreshed concurrently.")
        except Exception as e:
            logger.warning(
                f"Concurrent refresh failed (likely missing index), trying standard: {e}"
            )
            # Failed REFRESH leaves transaction aborted; clear it before retry.
            try:
                await self.session.rollback()
            except Exception:
                pass

            try:
                await self.session.execute(
                    text("REFRESH MATERIALIZED VIEW sefer_istatistik_mv")
                )
                logger.info("Sefer Stats MV refreshed standard.")
            except Exception as e2:
                logger.error(f"Sefer Stats MV refresh failed completely: {e2}")
                try:
                    await self.session.rollback()
                except Exception:
                    pass


def get_sefer_repo(session: Optional[AsyncSession] = None) -> SeferRepository:
    """SeferRepo provider. Always returns a new repository instance."""
    return SeferRepository(session=session)
