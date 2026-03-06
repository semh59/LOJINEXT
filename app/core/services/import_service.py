import io
import pandas as pd
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy import text
from app.database.unit_of_work import UnitOfWork
from app.core.services.excel_service import ExcelService
from app.core.container import get_container
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ImportService:
    """Service handling bulk data imports and rollback mechanisms."""

    SUPPORTED_TYPES = ["arac", "surucu", "sefer", "yakit"]

    def __init__(
        self,
        sefer_service=None,
        yakit_service=None,
        arac_repo=None,
        sofor_repo=None,
        arac_service=None,
        sofor_service=None,
        dorse_repo=None,
    ):
        self.sefer_service = sefer_service
        self._sefer_service = sefer_service
        self.yakit_service = yakit_service
        self._yakit_service = yakit_service
        self.arac_repo = arac_repo
        self._arac_repo = arac_repo
        self.sofor_repo = sofor_repo
        self._sofor_repo = sofor_repo
        self.arac_service = arac_service
        self._arac_service = arac_service
        self.sofor_service = sofor_service
        self._sofor_service = sofor_service
        self.dorse_repo = dorse_repo
        self._dorse_repo = dorse_repo
        self.guzergah_service = None
        self._guzergah_service = None

    async def parse_and_preview(
        self, file: UploadFile, aktarim_tipi: str
    ) -> Dict[str, Any]:
        """Reads Excel/CSV file and provides a mapping preview without writing to DB."""
        if aktarim_tipi not in self.SUPPORTED_TYPES:
            raise HTTPException(
                status_code=400, detail=f"Desteklenmeyen aktarım tipi: {aktarim_tipi}"
            )

        content = await file.read()
        try:
            if file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            else:
                df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            logger.error(f"Dosya okuma hatası: {e}")
            raise HTTPException(status_code=400, detail="Dosya formatı geçersiz.")

        df = df.fillna("")
        headers = df.columns.tolist()
        total_rows = len(df)
        preview_data = df.head(5).to_dict(orient="records")

        return {
            "filename": file.filename,
            "aktarim_tipi": aktarim_tipi,
            "headers": headers,
            "total_rows": total_rows,
            "preview": preview_data,
        }

    async def execute_import(
        self, file: UploadFile, aktarim_tipi: str, user_id: int, mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Executes the import against mapping inside a single transaction.
        Tracks inserted IDs to allow future rollbacks.
        """
        if aktarim_tipi not in self.SUPPORTED_TYPES:
            raise HTTPException(status_code=400, detail="Desteklenmeyen aktarım tipi.")

        content = await file.read()
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        df = df.fillna("")

        async with UnitOfWork() as uow:
            # 1. Kayıt Geçmişi Oluştur
            job_data = {
                "dosya_adi": file.filename,
                "aktarim_tipi": aktarim_tipi,
                "durum": "PROCESSING",
                "toplam_kayit": len(df),
                "yukleyen_id": user_id,
            }
            job = await uow.import_repo.create_import_job(job_data)
            await uow.commit()  # Flush job id safely first to memory track progress

            basarili = 0
            hatali = 0
            inserted_ids = []
            hatalar = {}

            # Execute Raw Inserts based on active mappings mapped correctly
            # Simulating specific inserts to showcase mapping usage dynamically
            for index, row in df.iterrows():
                try:
                    if aktarim_tipi == "arac":
                        plaka = row.get(mapping.get("plaka", "plaka"))
                        kapasite = float(
                            row.get(mapping.get("kapasite", "kapasite"), 0)
                        )

                        if not plaka:
                            raise ValueError("Plaka alanı zorunludur.")

                        # Standard DB insert operation logic
                        stmt = text(
                            "INSERT INTO araclar (plaka, kapasite, durum) VALUES (:plaka, :kapasite, 'AKTIF') RETURNING id"
                        )
                        result = await uow.session.execute(
                            stmt, {"plaka": plaka, "kapasite": kapasite}
                        )
                        inserted_ids.append(result.scalar())
                        basarili += 1

                    elif aktarim_tipi == "surucu":
                        ad_soyad = row.get(mapping.get("ad_soyad", "ad_soyad"))
                        ehliyet_sinifi = row.get(
                            mapping.get("ehliyet_sinifi", "ehliyet_sinifi")
                        )
                        telefon = row.get(mapping.get("telefon", "telefon"))

                        stmt = text(
                            "INSERT INTO soforler (ad_soyad, ehliyet_sinifi, telefon, durum) VALUES (:ad_soyad, :ehliyet, :tel, 'AKTIF') RETURNING id"
                        )
                        result = await uow.session.execute(
                            stmt,
                            {
                                "ad_soyad": ad_soyad,
                                "ehliyet": ehliyet_sinifi,
                                "tel": telefon,
                            },
                        )
                        inserted_ids.append(result.scalar())
                        basarili += 1

                    elif aktarim_tipi == "sefer":
                        plaka = row.get(mapping.get("plaka", "plaka"))
                        sofor_ad = row.get(mapping.get("sofor_ad", "sofor_ad"))
                        dorse_plaka = row.get(
                            mapping.get("dorse_plakasi", "dorse_plakasi")
                        )
                        tarih = _parse_date_flexible(
                            row.get(mapping.get("tarih", "tarih"))
                        )
                        mesafe = self._validate_numeric(
                            row.get(mapping.get("mesafe_km", "mesafe_km"), 0), "Mesafe"
                        )
                        ton = self._validate_numeric(
                            row.get(mapping.get("ton", "ton"), 0), "Yük"
                        )

                        # Resolve IDs
                        vehicles = await self.arac_repo.get_all(include_inactive=True)
                        arac_id = self._resolve_arac_id(plaka, vehicles)

                        sofor_id = None
                        if sofor_ad:
                            drivers = await self.sofor_repo.get_all(
                                include_inactive=True
                            )
                            sofor_id = self._resolve_sofor_id(sofor_ad, drivers)

                        dorse_id = None
                        if dorse_plaka:
                            trailers = await self.dorse_repo.get_all(
                                include_inactive=True
                            )
                            dorse_id = self._resolve_dorse_id(dorse_plaka, trailers)

                        stmt = text(
                            """INSERT INTO seferler (arac_id, sofor_id, dorse_id, tarih, mesafe_km, net_kg, durum) 
                               VALUES (:arac_id, :sofor_id, :dorse_id, :tarih, :mesafe, :ton, 'Tamam') RETURNING id"""
                        )
                        result = await uow.session.execute(
                            stmt,
                            {
                                "arac_id": arac_id,
                                "sofor_id": sofor_id,
                                "dorse_id": dorse_id,
                                "tarih": tarih,
                                "mesafe": mesafe,
                                "ton": ton,
                            },
                        )
                        sefer_id = result.scalar()
                        inserted_ids.append(sefer_id)
                        basarili += 1

                        # Trigger Physics recalculated event
                        from app.infrastructure.events.event_bus import (
                            get_event_bus,
                            Event,
                            EventType,
                        )

                        await get_event_bus().publish_async(
                            Event(
                                type=EventType.SEFER_UPDATED,
                                data={"sefer_id": sefer_id, "trigger": "bulk_import"},
                            )
                        )

                    elif aktarim_tipi == "yakit":
                        plaka = row.get(mapping.get("plaka", "plaka"))
                        tarih = _parse_date_flexible(
                            row.get(mapping.get("tarih", "tarih"))
                        )
                        litre = self._validate_numeric(
                            row.get(mapping.get("litre", "litre"), 0), "Litre"
                        )
                        tutar = self._validate_numeric(
                            row.get(mapping.get("toplam_tutar", "toplam_tutar"), 0),
                            "Tutar",
                        )
                        km = self._validate_numeric(
                            row.get(mapping.get("km_sayac", "km_sayac"), 0), "Kilometre"
                        )

                        vehicles = await self.arac_repo.get_all(include_inactive=True)
                        arac_id = self._resolve_arac_id(plaka, vehicles)

                        stmt = text(
                            """INSERT INTO yakit_alimlar (arac_id, tarih, litre, toplam_tutar, km_sayac) 
                               VALUES (:arac_id, :tarih, :litre, :tutar, :km) RETURNING id"""
                        )
                        result = await uow.session.execute(
                            stmt,
                            {
                                "arac_id": arac_id,
                                "tarih": tarih,
                                "litre": litre,
                                "tutar": tutar,
                                "km": km,
                            },
                        )
                        inserted_ids.append(result.scalar())
                        basarili += 1

                except Exception as e:
                    hatali += 1
                    hatalar[str(index)] = str(e)

            # 3. Güncelle
            await uow.import_repo.update_job_status(
                job.id,
                durum="COMPLETED" if hatali == 0 else "COMPLETED_WITH_ERRORS",
                basarili_kayit=basarili,
                hatali_kayit=hatali,
                islem_haritasi={"inserted_ids": inserted_ids},
                hatalar=hatalar,
            )

            await uow.commit()
            return {
                "job_id": job.id,
                "basarili": basarili,
                "hatali": hatali,
                "errors": hatalar,
            }

    async def rollback_import(self, job_id: int, user_id: int) -> bool:
        """
        Reverts a previous import by cascading deletions on the tracked IDs.
        """
        async with UnitOfWork() as uow:
            job = await uow.import_repo.get_by_id(job_id)
            if not job:
                raise HTTPException(
                    status_code=404, detail="Aktarım geçmişi bulunamadı."
                )

            if job.durum == "ROLLED_BACK":
                raise HTTPException(
                    status_code=400, detail="Bu aktarım zaten geri alındı."
                )

            if not job.islem_haritasi or "inserted_ids" not in job.islem_haritasi:
                raise HTTPException(
                    status_code=400, detail="Geri alınacak veri haritası yok."
                )

            inserted_ids = job.islem_haritasi["inserted_ids"]

            if not inserted_ids:
                return True  # Nothing to delete

            try:
                if job.aktarim_tipi == "arac":
                    stmt = text("DELETE FROM araclar WHERE id = ANY(:ids)")
                    await uow.session.execute(stmt, {"ids": inserted_ids})
                elif job.aktarim_tipi == "surucu":
                    stmt = text("DELETE FROM soforler WHERE id = ANY(:ids)")
                    await uow.session.execute(stmt, {"ids": inserted_ids})
                elif job.aktarim_tipi == "sefer":
                    stmt = text("DELETE FROM seferler WHERE id = ANY(:ids)")
                    await uow.session.execute(stmt, {"ids": inserted_ids})
                elif job.aktarim_tipi == "yakit":
                    stmt = text("DELETE FROM yakit_alimlar WHERE id = ANY(:ids)")
                    await uow.session.execute(stmt, {"ids": inserted_ids})

                await uow.import_repo.update_job_status(
                    job.id,
                    durum="ROLLED_BACK",
                    degisiklik_sebebi=f"Geri alındı, yetkili: {user_id}",
                )
                await uow.commit()
                return True
            except Exception as e:
                logger.error(f"Rollback hatası (Job {job_id}): {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Rollback sırasında kritik veritabanı hatası oluştu.",
                )

    async def process_sefer_import(self, content: bytes):
        """Processes Excel import for trips (Seferler)."""
        try:
            items = await ExcelService.parse_sefer_excel(content)
            if not items:
                return 0, ["Excel dosyasında veri bulunamadı."]

            errors = []
            sefer_list = []

            # Pre-fetch for resolution (Handle None for tests)
            vehicles = (
                await self.arac_repo.get_all(include_inactive=True)
                if self.arac_repo
                else []
            )
            drivers = (
                await self.sofor_repo.get_all(include_inactive=True)
                if self.sofor_repo
                else []
            )
            trailers = (
                await self.dorse_repo.get_all(include_inactive=True)
                if self.dorse_repo
                else []
            )

            for idx, item in enumerate(items, 1):
                try:
                    # Validate and Resolve
                    plaka = self._validate_plaka(item.get("plaka"))
                    arac_id = self._resolve_arac_id(plaka, vehicles)

                    sofor_id = None
                    if item.get("sofor_adi"):
                        name = self._validate_name(item.get("sofor_adi"))
                        sofor_id = self._resolve_sofor_id(name, drivers)

                    dorse_id = None
                    if item.get("dorse_plakasi"):
                        d_plaka = self._validate_plaka(item.get("dorse_plakasi"))
                        dorse_id = self._resolve_dorse_id(d_plaka, trailers)

                    # Create Sefer Data
                    sefer_data = {
                        "arac_id": arac_id,
                        "sofor_id": sofor_id,
                        "dorse_id": dorse_id,
                        "tarih": item.get("tarih"),
                        "baslangic_km": self._validate_numeric(
                            item.get("baslangic_km", 0), "Kilometre"
                        ),
                        "bitis_km": self._validate_numeric(
                            item.get("bitis_km", 0), "Kilometre"
                        ),
                        "mesafe_km": self._validate_numeric(
                            item.get("mesafe_km", 1.0), "Mesafe"
                        ),
                        "yuk_miktari": self._validate_numeric(
                            item.get("net_kg", 0), "Yük"
                        ),
                        "cikis_yeri": item.get("cikis_yeri", "Bilinmiyor"),
                        "varis_yeri": item.get("varis_yeri", "Bilinmiyor"),
                        "durum": "Tamam",
                    }
                    sefer_list.append(sefer_data)

                except ValueError as ve:
                    # Parse field if possible from message
                    msg = str(ve)
                    field = "Bilinmiyor"
                    if "Plaka" in msg or "Araç" in msg:
                        field = "plaka"
                    elif "Şoför" in msg:
                        field = "sofor_adi"
                    elif "ay" in msg or "Yük" in msg:
                        field = "net_kg"

                    errors.append({"row": idx, "field": field, "reason": msg})
                except Exception as e:
                    errors.append(
                        {
                            "row": idx,
                            "field": "genel",
                            "reason": f"Beklenmedik hata: {str(e)}",
                        }
                    )

            count = 0
            if sefer_list:
                # Delegate to SeferService for bulk processing
                count = await self.sefer_service.bulk_add_sefer(sefer_list)

            return count, errors

        except Exception as e:
            logger.error(f"Sefer import error: {e}")
            return 0, [f"Sistem hatası: {str(e)}"]

    async def process_yakit_import(self, content: bytes):
        """Processes Excel import for fuel records."""
        try:
            items = await ExcelService.parse_yakit_excel(content)
            if not items:
                return 0, ["Excel dosyasında veri bulunamadı."]

            errors = []
            yakit_list = []
            vehicles = await self.arac_repo.get_all(include_inactive=True)

            for idx, item in enumerate(items, 1):
                try:
                    plaka = self._validate_plaka(item.get("plaka"))
                    arac_id = self._resolve_arac_id(plaka, vehicles)

                    yakit_data = {
                        "arac_id": arac_id,
                        "tarih": item.get("tarih"),
                        "istasyon": item.get("istasyon"),
                        "litre": self._validate_numeric(item.get("litre", 0), "Litre"),
                        "fiyat_tl": self._validate_numeric(
                            item.get("fiyat_tl", 0), "Fiyat"
                        ),
                        "km_sayac": self._validate_numeric(
                            item.get("km_sayac", 0), "Kilometre"
                        ),
                    }
                    yakit_list.append(yakit_data)
                except ValueError as ve:
                    errors.append(f"Satır {idx}: {str(ve)}")

            count = 0
            if yakit_list:
                count = await self.yakit_service.bulk_add_yakit(yakit_list)
            return count, errors
        except Exception as e:
            return 0, [f"Sistem hatası: {str(e)}"]

    async def process_vehicle_import(self, content: bytes):
        """Processes vehicle import."""
        try:
            items = await ExcelService.parse_vehicle_data(content)
            if not items:
                return 0, ["Excel dosyasında veri bulunamadı."]

            errors = []
            count = 0
            existing_vehicles = await self.arac_repo.get_all(include_inactive=True)

            to_add = []
            async with UnitOfWork() as uow:
                for idx, item in enumerate(items, 1):
                    try:
                        plaka = self._validate_plaka(item.get("plaka"))

                        # Check if exists (reactivate if inactive)
                        existing = next(
                            (
                                v
                                for v in existing_vehicles
                                if v["plaka"].replace(" ", "").upper() == plaka
                            ),
                            None,
                        )
                        if existing:
                            if not existing.get("aktif", True):
                                await self.arac_repo.update(existing["id"], aktif=True)
                                errors.append(
                                    f"Araç {plaka} zaten mevcuttu, aktifleştirildi."
                                )
                            continue

                        to_add.append(item)
                    except ValueError as ve:
                        errors.append(f"Satır {idx}: {str(ve)}")

                if to_add:
                    count = await self.arac_service.bulk_add_arac(to_add)
                    await uow.commit()  # Commit reactivation or other changes
            return count, errors
        except Exception as e:
            return 0, [f"Sistem hatası: {str(e)}"]

    async def process_driver_import(self, content: bytes):
        """Processes driver import."""
        try:
            items = await ExcelService.parse_driver_data(content)
            if not items:
                return 0, ["Excel dosyasında veri bulunamadı."]

            errors = []
            count = await self.sofor_service.bulk_add_sofor(items)
            return count, errors
        except Exception as e:
            return 0, [f"Sistem hatası: {str(e)}"]

    async def import_routes(self, content: bytes):
        """Processes route import."""
        try:
            items = await ExcelService.parse_route_excel(content)
            if not items:
                return 0, ["Excel dosyası boş veya veri bulunamadı."]

            errors = []
            count = 0
            if not self._guzergah_service:
                self._guzergah_service = get_container().route_service

            # Keep both aligned
            self.guzergah_service = self._guzergah_service

            for idx, item in enumerate(items, 1):
                try:
                    await self._guzergah_service.create_guzergah(**item)
                    count += 1
                except Exception as e:
                    errors.append(f"Satır {idx}: {str(e)}")
            return count, errors
        except Exception as e:
            return 0, [f"Sistem hatası: {str(e)}"]

    def _resolve_arac_id(self, plaka, vehicles):
        if not plaka:
            return None
        search_p = plaka.replace(" ", "").upper()
        for v in vehicles:
            if v["plaka"].replace(" ", "").upper() == search_p:
                return v["id"]
        raise ValueError("Araç bulunamadı")

    def _resolve_sofor_id(self, name, drivers):
        if not name:
            return None
        search_n = name.strip().upper()
        for d in drivers:
            if d["ad_soyad"].strip().upper() == search_n:
                return d["id"]
        raise ValueError("Şoför bulunamadı")

    def _resolve_dorse_id(self, plaka, trailers):
        if not plaka:
            return None
        search_p = plaka.replace(" ", "").upper()
        for t in trailers:
            if t["plaka"].replace(" ", "").upper() == search_p:
                return t["id"]
        return None  # Optional for Sefer

    def _validate_plaka(self, plaka):
        if not plaka:
            raise ValueError("Plaka boş olamaz")
        p = str(plaka).replace(" ", "").upper()
        if len(p) < 5:
            raise ValueError("Plaka uzunluğu geçersiz")
        import re

        if not re.match(r"^[0-9]{2}[A-Z]{1,3}[0-9]{2,4}$", p):
            raise ValueError("Plaka formatı geçersiz")
        return p

    def _validate_name(self, name):
        if not name or len(str(name).strip()) < 2:
            raise ValueError("İsim en az 2 karakter olmalı")
        return str(name).strip().title()

    def _validate_location(self, loc):
        return loc

    def _validate_numeric(self, val, field):
        try:
            return float(val)
        except (ValueError, TypeError):
            raise ValueError(f"{field} sayı olmalı")


def _parse_date_flexible(val):
    """Helper to parse dates from various Excel formats."""
    from app.core.services.excel_service import _parse_date_flexible as pdf

    return pdf(val)


_import_service: Optional[ImportService] = None


def get_import_service() -> ImportService:
    """Thread-safe singleton getter for ImportService"""
    from app.core.container import get_container

    return get_container().import_service
