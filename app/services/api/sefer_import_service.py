from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from datetime import datetime
from app.core.services.excel_service import ExcelService
from app.infrastructure.logging.logger import get_logger
from app.core.container import get_container

logger = get_logger(__name__)


class SeferImportService:
    """Excel'den seferleri parse eden ve veritabanına işleyen özel servis."""

    def __init__(
        self, sefer_service=None, arac_repo=None, sofor_repo=None, dorse_repo=None
    ):
        self.sefer_service = sefer_service
        self.arac_repo = arac_repo
        self.sofor_repo = sofor_repo
        self.dorse_repo = dorse_repo

    async def process_excel_import(
        self, content: bytes, current_user_id: int
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Excel verisini işler ve Sefer modellerini oluşturur."""
        try:
            # Excel'i parse et
            items = await ExcelService.parse_sefer_excel(content)
            if not items:
                return 0, [
                    {"row": 0, "reason": "Excel dosyasında geçerli veri bulunamadı."}
                ]

            errors = []
            valid_sefers = []

            # Master datayı önceden çek (Performans için)
            vehicles = await self.arac_repo.get_all(include_inactive=True)
            drivers = await self.sofor_repo.get_all(include_inactive=True)
            trailers = await self.dorse_repo.get_all(include_inactive=True)

            for idx, item in enumerate(items, 1):
                try:
                    # 1. Araç Çözümleme
                    plaka = self._clean_plaka(item.get("plaka"))
                    arac_id = self._resolve_master_id(plaka, vehicles, "plaka")
                    if not arac_id:
                        raise ValueError(f"Araç bulunamadı: {plaka}")

                    # 2. Şoför Çözümleme (Opsiyonel ama önerilir)
                    sofor_id = None
                    sofor_adi = item.get("sofor_adi")
                    if sofor_adi:
                        sofor_id = self._resolve_master_id(
                            sofor_adi, drivers, "ad_soyad"
                        )
                        if not sofor_id:
                            logger.warning(
                                f"İçe aktarma: Şoför bulunamadı, boş geçiliyor: {sofor_adi}"
                            )

                    # 3. Dorse Çözümleme
                    dorse_id = None
                    dorse_plaka = self._clean_plaka(item.get("dorse_plakasi"))
                    if dorse_plaka:
                        dorse_id = self._resolve_master_id(
                            dorse_plaka, trailers, "plaka"
                        )

                    # 4. Veri Hazırlama
                    sefer_data = {
                        "tarih": item.get("tarih") or datetime.now().date(),
                        "arac_id": arac_id,
                        "sofor_id": sofor_id,
                        "dorse_id": dorse_id,
                        "cikis_yeri": item.get("cikis_yeri", "Bilinmiyor"),
                        "varis_yeri": item.get("varis_yeri", "Bilinmiyor"),
                        "mesafe_km": float(item.get("mesafe_km", 0)),
                        "net_kg": float(item.get("net_kg", 0)),
                        "durum": "Tamam",
                        "notlar": f"Excel Import - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    }
                    valid_sefers.append(sefer_data)

                except Exception as e:
                    errors.append({"row": idx + 1, "reason": str(e)})

            # 5. Toplu Ekleme
            if valid_sefers:
                count = await self.sefer_service.bulk_add_sefer(valid_sefers)
                return count, errors

            return 0, errors

        except Exception as e:
            logger.error(f"SeferImportService Error: {e}", exc_info=True)
            return 0, [{"row": 0, "reason": f"Sistem hatası: {str(e)}"}]

    def _clean_plaka(self, plaka: Any) -> str:
        if not plaka:
            return ""
        return str(plaka).replace(" ", "").upper()

    def _resolve_master_id(
        self, search_val: str, master_list: List[Any], field: str
    ) -> Optional[int]:
        if not search_val:
            return None
        search_norm = str(search_val).strip().upper()
        for item in master_list:
            item_val = (
                str(
                    getattr(item, field, "")
                    if hasattr(item, field)
                    else item.get(field, "")
                )
                .strip()
                .upper()
            )
            if item_val == search_norm:
                return item.id if hasattr(item, "id") else item.get("id")
        return None


def get_sefer_import_service() -> SeferImportService:
    container = get_container()
    return SeferImportService(
        sefer_service=container.sefer_service,
        arac_repo=container.arac_repo,
        sofor_repo=container.sofor_repo,
        dorse_repo=container.dorse_repo,
    )
