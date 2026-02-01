"""
TIR Yakıt Takip Sistemi - Import Servisi
Excel import işlemleri, validasyon ve ID eşleştirme mantığı.
"""
import re
from typing import Any, List, Tuple

from app.core.entities.models import SeferCreate, YakitAlimiCreate
from app.core.services.excel_service import ExcelService
from app.core.services.sefer_service import get_sefer_service
from app.core.services.yakit_service import get_yakit_service
from app.database.repositories.arac_repo import get_arac_repo
from app.database.repositories.sofor_repo import get_sofor_repo
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ImportService:
    """
    Excel import işlemlerini yöneten servis.
    UI katmanından business logic'i izole eder.
    Input validation ve güvenlik kontrolleri içerir.
    """
    
    # Güvenli karakter pattern'leri
    PLAKA_PATTERN = re.compile(r'^[0-9]{2}[A-ZĞÜŞÖÇİ]{1,3}[0-9]{2,4}$')
    NAME_PATTERN = re.compile(r'^[\w\sğüşöçıİĞÜŞÖÇ\-\.]+$', re.UNICODE)
    LOCATION_PATTERN = re.compile(r'^[\w\sğüşöçıİĞÜŞÖÇ\-\.\,\/\(\)]+$', re.UNICODE)
    
    # Limit sabitleri
    MAX_NAME_LENGTH = 100
    MAX_LOCATION_LENGTH = 200
    MAX_ROWS = 10000  # DoS prevention

    def __init__(
        self,
        arac_repo=None,
        sofor_repo=None,
        sefer_service=None,
        yakit_service=None,
        arac_service=None,
        sofor_service=None,
    ):
        self.arac_repo = arac_repo or get_arac_repo()
        self.sofor_repo = sofor_repo or get_sofor_repo()
        self.sefer_service = sefer_service or get_sefer_service()
        self.yakit_service = yakit_service or get_yakit_service()

        # Lazy initialization to avoid circular dependency
        self._arac_service = arac_service
        self._sofor_service = sofor_service

    @property
    def arac_service(self):
        """Lazy load arac_service to avoid circular dependency"""
        if self._arac_service is None:
            from app.core.services.arac_service import get_arac_service

            self._arac_service = get_arac_service()
        return self._arac_service

    @property
    def sofor_service(self):
        """Lazy load sofor_service to avoid circular dependency"""
        if self._sofor_service is None:
            from app.core.services.sofor_service import get_sofor_service

            self._sofor_service = get_sofor_service()
        return self._sofor_service

    # =========================================================================
    # INPUT VALIDATION METHODS
    # =========================================================================
    
    def _validate_plaka(self, plaka: str) -> str:
        """Plaka formatını doğrula ve normalize et"""
        if not plaka:
            raise ValueError("Plaka boş olamaz")
        
        plaka = str(plaka).strip().upper().replace(" ", "")
        
        # Uzunluk kontrolü
        if len(plaka) < 5 or len(plaka) > 10:
            raise ValueError(f"Geçersiz plaka uzunluğu: {plaka}")
        
        # Format kontrolü
        if not self.PLAKA_PATTERN.match(plaka):
            raise ValueError(f"Geçersiz plaka formatı: {plaka}")
        
        return plaka
    
    def _validate_name(self, name: str, field_name: str = "İsim") -> str:
        """İsim güvenlik kontrolü"""
        if not name:
            raise ValueError(f"{field_name} boş olamaz")
        
        name = str(name).strip()
        
        if len(name) < 2:
            raise ValueError(f"{field_name} en az 2 karakter olmalı")
        
        if len(name) > self.MAX_NAME_LENGTH:
            raise ValueError(f"{field_name} çok uzun (max {self.MAX_NAME_LENGTH})")
        
        if not self.NAME_PATTERN.match(name):
            raise ValueError(f"{field_name} geçersiz karakterler içeriyor")
        
        return name.title()  # Ahmet Yılmaz formatı
    
    def _validate_location(self, location: str, field_name: str = "Konum") -> str:
        """Konum güvenlik kontrolü"""
        if not location:
            raise ValueError(f"{field_name} boş olamaz")
        
        location = str(location).strip()
        
        if len(location) > self.MAX_LOCATION_LENGTH:
            raise ValueError(f"{field_name} çok uzun")
        
        if not self.LOCATION_PATTERN.match(location):
            raise ValueError(f"{field_name} geçersiz karakterler içeriyor")
        
        return location
    
    def _validate_numeric(
        self, 
        value: Any, 
        field_name: str, 
        min_val: float = 0, 
        max_val: float = float('inf')
    ) -> float:
        """Sayısal değer doğrulama"""
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} sayı olmalı")
        
        if num < min_val or num > max_val:
            raise ValueError(f"{field_name} geçersiz aralık: {min_val}-{max_val}")
        
        return num

    def _resolve_arac_id(self, plaka: str, vehicles: List[Any]) -> int:
        """Plakadan Araç ID bul"""
        # vehicles can be Arac objects or dicts, depends on repo
        # AracRepository.get_all -> super().get_all -> dicts

        # vehicles parametresi cache optimization için dışarıdan verilmeli
        if not plaka:
            raise ValueError("Plaka boş olamaz")

        normalized_plaka = plaka.replace(" ", "").upper()

        for v in vehicles:
            v_plaka = v["plaka"] if isinstance(v, dict) else v.plaka
            if v_plaka.replace(" ", "").upper() == normalized_plaka:
                return v["id"] if isinstance(v, dict) else v.id

        raise ValueError(f"Araç bulunamadı: {plaka}")

    def _resolve_sofor_id(self, ad_soyad: str, drivers: List[Any]) -> int:
        """İsimden Şoför ID bul"""
        if not ad_soyad:
            raise ValueError("Şoför adı boş olamaz")

        normalized_name = ad_soyad.lower().strip()

        for d in drivers:
            d_ad = d["ad_soyad"] if isinstance(d, dict) else d.ad_soyad
            if d_ad.lower().strip() == normalized_name:
                return d["id"] if isinstance(d, dict) else d.id

        raise ValueError(f"Şoför bulunamadı: {ad_soyad}")

    async def process_sefer_import(self, file_content: bytes) -> Tuple[int, List[str]]:
        """
        Sefer Excel dosyasını işle ve veritabanına kaydet.

        Returns:
            (success_count, error_list)
        """
        try:
            # 1. Parse Excel (FAZ 2.1: Async parsing)
            data_list = await ExcelService.parse_sefer_excel(file_content)

            if not data_list:
                return 0, ["Excel dosyasında veri bulunamadı"]

            # 2. Pre-fetch Lookup Data (Performance)
            vehicles = await self.arac_repo.get_all(sadece_aktif=True)
            drivers = await self.sofor_repo.get_all(sadece_aktif=True)

            validated_items = []
            errors = []

            # 3. Validate & Resolve IDs
            for index, item in enumerate(data_list):
                row_num = index + 2  # Header + 0-index
                try:
                    # Resolve IDs
                    if "plaka" in item:
                        item["arac_id"] = self._resolve_arac_id(item["plaka"], vehicles)

                    if "sofor_adi" in item:
                        item["sofor_id"] = self._resolve_sofor_id(item["sofor_adi"], drivers)

                    if "arac_id" not in item:
                        raise ValueError("Araç belirtilmemiş")
                    if "sofor_id" not in item:
                        raise ValueError("Şoför belirtilmemiş")

                    # Create DTO (Pydantic Validation happens here)
                    dto = SeferCreate(**item)
                    validated_items.append(dto)

                except Exception as e:
                    errors.append(f"Satır {row_num}: {str(e)}")

            if errors:
                return 0, errors

            # 4. Bulk Insert via Service
            count = await self.sefer_service.bulk_add_sefer(validated_items)
            return count, []

        except Exception as e:
            logger.error(f"Import process error: {e}", exc_info=True)
            return 0, [f"Sistem hatası: {str(e)}"]

    async def process_yakit_import(self, file_content: bytes) -> Tuple[int, List[str]]:
        """
        Yakıt Excel dosyasını işle ve veritabanına kaydet.
        """
        try:
            # FAZ 2.1: Async parsing
            data_list = await ExcelService.parse_yakit_excel(file_content)

            if not data_list:
                return 0, ["Excel dosyasında veri bulunamadı"]

            vehicles = await self.arac_repo.get_all(sadece_aktif=True)

            validated_items = []
            errors = []

            for index, item in enumerate(data_list):
                row_num = index + 2
                try:
                    if "plaka" in item:
                        item["arac_id"] = self._resolve_arac_id(item["plaka"], vehicles)

                    if "arac_id" not in item:
                        raise ValueError("Araç belirtilmemiş")

                    dto = YakitAlimiCreate(**item)
                    validated_items.append(dto)

                except Exception as e:
                    errors.append(f"Satır {row_num}: {str(e)}")

            if errors:
                return 0, errors

            count = await self.yakit_service.bulk_add_yakit(validated_items)
            return count, []

        except Exception as e:
            logger.error(f"Import process error: {e}", exc_info=True)
            return 0, [f"Sistem hatası: {str(e)}"]

    async def process_vehicle_import(self, file_content: bytes) -> Tuple[int, List[str]]:
        """Araç Excel dosyasını işle (N+1 Prevention)"""
        try:
            # ExcelService bytes parser needed or use UploadFile wrapper.
            # For now using parse_vehicle_data (UploadFile) with wrapper.
            # TODO: Convert ExcelService upload_file methods to bytes.

            from app.core.entities.models import AracCreate
            import io
            from fastapi import UploadFile

            # Temporary workaround until ExcelService is purely bytes-based
            dummy_file = UploadFile(filename="temp.xlsx", file=io.BytesIO(file_content))
            data_list = await ExcelService.parse_vehicle_data(dummy_file)

            if not data_list:
                return 0, ["Excel dosyasında veri bulunamadı"]

            # 2. Pre-fetch existing plates to avoid N+1
            existing_araclar = await self.arac_repo.get_all(sadece_aktif=False) # Get ALL including passive
            # Map normalized plate -> object/dict
            existing_plates = {
                (a["plaka"] if isinstance(a, dict) else a.plaka).replace(" ", "").upper() : a 
                for a in existing_araclar
            }

            validated_items = []
            errors = []

            for index, item in enumerate(data_list):
                row_num = index + 2
                try:
                    plate_norm = item["plaka"].replace(" ", "").upper()
                    
                    if plate_norm in existing_plates:
                        # Eğer araç varsa ama pasifse AKTİFLEŞTİR
                        existing_obj = existing_plates[plate_norm]
                        # Support dict or object access
                        is_active = (existing_obj.get('aktif') if isinstance(existing_obj, dict) else existing_obj.aktif)
                        obj_id = (existing_obj.get('id') if isinstance(existing_obj, dict) else existing_obj.id)
                        
                        if not is_active:
                             logger.info(f"Reactivating vehicle: {plate_norm}")
                             # FIX: We must reactivate AND update data to ensure validity (heal corrupt records)
                             # Extract fields from the NEW item to update the old record
                             # Convert item (dict) to update args
                             # We can use AracUpdate or just pass kwargs
                             update_data = {
                                 "aktif": True,
                                 "marka": item.get("marka"),
                                 "model": item.get("model", ""),
                                 "yil": item.get("yil"),
                                 "tank_kapasitesi": item.get("tank_kapasitesi"),
                                 "hedef_tuketim": item.get("hedef_tuketim"),
                                 "bos_agirlik_kg": item.get("bos_agirlik_kg"),
                                 "motor_verimliligi": item.get("motor_verimliligi"),
                                 "notlar": item.get("notlar", "")
                             }
                             # Remove None values to avoid overwriting with None if not intended?
                             # Actually Excel parsing sets defaults. So we should use them.
                             
                             await self.arac_repo.update(obj_id, **update_data)
                             
                             # Don't add to create list, as it's updated.
                             errors.append(f"Satır {row_num}: {item['plaka']} pasifti, güncellenerek aktifleştirildi.")
                        else:
                             errors.append(f"Satır {row_num}: {item['plaka']} zaten aktif, atlandı.")
                        continue

                    dto = AracCreate(**item)
                    validated_items.append(dto)
                except Exception as e:
                    errors.append(f"Satır {row_num}: {str(e)}")

            if validated_items:
                # bulk_create logic AracRepo/AracService içinde olmalı.
                # Genellikle Service.add loop içinde repository'yi çağırır.
                # Faz 1'deki gibi bulk_create eklemeliyiz.
                count = await self.arac_service.bulk_add_arac(validated_items)
                return count, errors

            return 0, errors

        except Exception as e:
            logger.error(f"Vehicle import error: {e}")
            return 0, [str(e)]

    async def process_driver_import(self, file_content: bytes) -> Tuple[int, List[str]]:
        """Şoför Excel dosyasını işle"""
        try:
            from app.core.entities.models import SoforCreate
            import io
            from fastapi import UploadFile

            dummy_file = UploadFile(filename="temp.xlsx", file=io.BytesIO(file_content))
            data_list = await ExcelService.parse_driver_data(dummy_file)

            if not data_list:
                return 0, ["Excel dosyasında veri bulunamadı"]

            # 2. Pre-fetch existing drivers to avoid name collision N+1 (Optional but good)
            existing_drivers = await self.sofor_repo.get_all()
            existing_names = {d["ad_soyad"].lower().strip() for d in existing_drivers}

            validated_items = []
            errors = []

            for index, item in enumerate(data_list):
                row_num = index + 2
                try:
                    name_norm = item["ad_soyad"].lower().strip()
                    if name_norm in existing_names:
                        errors.append(
                            f"Satır {row_num}: {item['ad_soyad']} zaten kayıtlı, atlandı."
                        )
                        continue

                    dto = SoforCreate(**item)
                    validated_items.append(dto)
                except Exception as e:
                    errors.append(f"Satır {row_num}: {str(e)}")

            if validated_items:
                count = await self.sofor_service.bulk_add_sofor(validated_items)
                return count, errors

            return 0, errors

        except Exception as e:
            logger.error(f"Driver import error: {e}")
            return 0, [str(e)]


# Singleton
def get_import_service() -> ImportService:
    from app.core.container import get_container

    return get_container().import_service
