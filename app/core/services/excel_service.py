"""
TIR Yakıt Takip - Konsolide Excel Servisi
Sefer, Yakıt, Araç ve Şoför Excel dosyalarını işler, şablon oluşturur.
"""

import difflib
import io
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SafeColumnMapper:
    """Fuzzy matching for Excel headers to internal keys"""

    COLS = {
        "tarih": [
            "tarih",
            "sefer tarihi",
            "alış tarihi",
            "tür",
            "gün",
            "date",
            "trip date",
            "fiş tarihi",
            "islem tarihi",
        ],
        "plaka": ["plaka", "plaka no", "araç plaka", "plate", "vehicle", "tasit plaka"],
        "litre": [
            "litre",
            "miktar",
            "yakıt miktarı",
            "liters",
            "amount",
            "volüm",
            "yakit miktari",
        ],
        "fiyat_tl": ["fiyat", "birim fiyat", "price", "unit price", "birim tutar"],
        "toplam_tutar": [
            "tutar",
            "toplam tutar",
            "toplam",
            "cost",
            "total cost",
            "amount paid",
            "brut tutar",
            "net tutar",
        ],
        "km_sayac": [
            "km",
            "km sayacı",
            "araç km",
            "odometer",
            "mileage",
            "km sayaci",
            "arac km",
        ],
        "istasyon": [
            "istasyon",
            "bayi",
            "servis alanı",
            "station",
            "provider",
            "tesis adi",
        ],
        "fis_no": [
            "fis no",
            "fiş no",
            "makbuz",
            "receipt",
            "inv no",
            "belge no",
            "evrak no",
        ],
        "depo_durumu": ["depo durumu", "depo", "tank status", "fullness"],
        "cikis_yeri": [
            "cikis yeri",
            "çıkış yeri",
            "başlangıç",
            "start",
            "origin",
            "from",
            "yukleme yeri",
        ],
        "varis_yeri": [
            "varis yeri",
            "varış yeri",
            "bitiş",
            "destination",
            "to",
            "bosaltma yeri",
        ],
        "sofor_adi": [
            "sofor adi",
            "şoför adı",
            "şoför",
            "driver",
            "operator",
            "surucu",
        ],
        "net_kg": [
            "yuk",
            "yük",
            "ağırlık",
            "net yük",
            "weight",
            "load",
            "kg",
            "ton",
            "tonaj",
        ],
        "saat": ["saat", "zaman", "time"],
        "durum": ["durum", "status"],
        "marka": ["marka", "brand"],
        "model": ["model"],
        "yil": ["yil", "yıl", "model yılı", "year"],
        "tank_kapasitesi": ["tank kapasitesi", "depo hacmi", "tank capacity"],
        "bos_agirlik_kg": ["bos agirlik", "boş ağırlık", "tare"],
        "motor_verimliligi": [
            "motor verimliligi",
            "motor verimliliği",
            "engine efficiency",
        ],
        "telefon": ["telefon", "phone", "gsm"],
        "ise_baslama": ["ise baslama", "işe başlama", "baslangic", "hire date"],
        "ehliyet_sinifi": ["ehliyet sinifi", "ehliyet", "license"],
        "dorse_plakasi": ["dorse", "dorse plaka", "dorse plakası", "trailer"],
        "dorse_tipi": ["dorse tipi", "dorse türü", "trailer type"],
        "lastik_sayisi": ["lastik sayisi", "lastik sayısı", "tires"],
    }

    @classmethod
    def map_columns(cls, df_columns: List[str]) -> Dict[str, str]:
        mapping = {}
        df_columns_clean = [str(c).strip().lower() for c in df_columns]

        for internal_key, aliases in cls.COLS.items():
            best_match = None
            highest_score = 0

            # 1. Look for exact matches first (highest priority)
            for alias in aliases:
                if alias in df_columns_clean:
                    idx = df_columns_clean.index(alias)
                    best_match = df_columns[idx]
                    highest_score = 1.0
                    break

            # 2. Partial/Fuzzy match (only if no exact match)
            if not best_match:
                for col_idx, col in enumerate(df_columns_clean):
                    for alias in aliases:
                        # Check if internal key is explicitly sub-part
                        if alias in col or col in alias:
                            score = (
                                max(len(alias) / len(col), len(col) / len(alias)) * 0.8
                            )
                        else:
                            score = difflib.SequenceMatcher(None, col, alias).ratio()

                        if score > 0.75 and score > highest_score:
                            highest_score = score
                            best_match = df_columns[col_idx]

            if best_match:
                mapping[best_match] = internal_key

        return mapping


# Desteklenen tarih formatları (multi-locale support)
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y-%m-%dT%H:%M:%S",
]


def _parse_date_flexible(val: Any) -> Optional[date]:
    """Farklı tarih formatlarını dene ve date'e çevir"""
    if not val or pd.isna(val):
        return None

    if isinstance(val, (datetime, date)):
        return val if isinstance(val, date) else val.date()

    if isinstance(val, pd.Timestamp):
        return val.date()

    if isinstance(val, str):
        val = val.strip()
        for fmt in DATE_FORMATS:
            try:
                if "T" in val and "T" not in fmt:
                    continue  # Skip simple formats for ISO strings
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


class ExcelService:
    """
    Excel dosyalarını okuyup backend modellerine uygun dict listesi döndürür.
    Tüm Excel operasyonları için tek kaynak.
    """

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit (Excel Bomb Guard)

    @staticmethod
    async def _read_excel_to_df(file: UploadFile) -> pd.DataFrame:
        """UploadFile nesnesini pandas DataFrame'e çevirir"""
        # Güvenlik Kontrolü: Dosya Boyutu
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > ExcelService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Dosya çok büyük. Maksimum limit: {ExcelService.MAX_FILE_SIZE / (1024 * 1024):.0f}MB",
            )

        try:
            contents = await file.read()
            # engine_kwargs ile güvenli okuma
            df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
            # Kolon isimlerini temizle: boşlukları at, küçük harfe çevir
            df.columns = df.columns.astype(str).str.strip().str.lower()
            # NaN değerleri None ile değiştir
            df = df.where(pd.notnull(df), None)
            return df
        except Exception as e:
            logger.error(f"Excel parsing error: {e}")
            raise HTTPException(
                status_code=400, detail=f"Excel dosyası okunamadı veya bozuk: {e!s}"
            )

    # =========================================================================
    # CORE PARSING (Bytes based - used by ImportService)
    # =========================================================================

    # =========================================================================
    # CORE PARSING (Bytes based - used by ImportService)
    # =========================================================================

    @staticmethod
    async def parse_sefer_excel(content: bytes) -> List[Dict[str, Any]]:
        """Seferler Excel dosyasını (bytes) parse et (Async & Non-blocking)."""
        import asyncio

        return await asyncio.to_thread(ExcelService._parse_sefer_excel_sync, content)

    @staticmethod
    def _parse_sefer_excel_sync(content: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")

            # Dynamic Column Mapping
            column_map = SafeColumnMapper.map_columns(df.columns.tolist())
            logger.info(f"Sefer Excel Map: {column_map}")

            result = []
            for _, row in df.iterrows():
                item = {}
                for excel_col, model_field in column_map.items():
                    val = row[excel_col]
                    if model_field == "tarih":
                        val = _parse_date_flexible(val)
                    if pd.isna(val):
                        val = None

                    # FAZ 2.2: Güvenli tip dönüşümü (Safe Cast)
                    if model_field == "mesafe_km" and val:
                        try:
                            val = float(val)
                        except Exception:
                            val = 0.0
                    if model_field == "net_kg" and val:
                        try:
                            val = float(val)
                        except Exception:
                            val = 0.0

                    item[model_field] = val

                # Validation: Requires at least Plaka and Tarih
                if item.get("plaka") and item.get("tarih"):
                    result.append(item)
            return result
        except Exception as e:
            logger.error(f"Sync sefer excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {e!s}")

    @staticmethod
    async def parse_yakit_excel(content: bytes) -> List[Dict[str, Any]]:
        """Yakıt Excel dosyasını (bytes) parse et (Async & Non-blocking)."""
        import asyncio

        return await asyncio.to_thread(ExcelService._parse_yakit_excel_sync, content)

    @staticmethod
    def _parse_yakit_excel_sync(content: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")

            column_map = SafeColumnMapper.map_columns(df.columns.tolist())
            logger.info(f"Yakit Excel Map: {column_map}")

            result = []
            for _, row in df.iterrows():
                item = {}
                for excel_col, model_field in column_map.items():
                    val = row[excel_col]
                    if model_field == "tarih":
                        val = _parse_date_flexible(val)
                    if pd.isna(val):
                        val = None

                    # FAZ 2.2: Güvenli tip dönüşümü (Safe Cast)
                    try:
                        if model_field == "litre" and val:
                            val = float(val)
                        if model_field == "fiyat_tl" and val:
                            val = float(val)
                        if model_field == "km_sayac" and val:
                            val = int(float(val))
                    except (ValueError, TypeError):
                        val = 0

                    item[model_field] = val

                if item.get("plaka") and item.get("tarih"):
                    result.append(item)
            return result
        except Exception as e:
            logger.error(f"Sync yakit excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {e!s}")

    @staticmethod
    async def parse_route_excel(content: bytes) -> List[Dict[str, Any]]:
        """Güzergahlar Excel dosyasını (bytes) parse et (Async & Non-blocking)."""
        import asyncio

        return await asyncio.to_thread(ExcelService._parse_route_excel_sync, content)

    @staticmethod
    def _parse_route_excel_sync(content: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            column_map = SafeColumnMapper.map_columns(df.columns.tolist())
            logger.info(f"Route Excel Map: {column_map}")

            result = []
            for _, row in df.iterrows():
                item = {}
                for excel_col, model_field in column_map.items():
                    val = row[excel_col]
                    if pd.isna(val):
                        val = None

                    if model_field == "mesafe_km" and val:
                        try:
                            val = float(val)
                        except Exception:
                            val = 0.0

                    item[model_field] = val

                if item.get("cikis_yeri") and item.get("varis_yeri"):
                    result.append(item)
            return result

            result = []
            for _, row in df.iterrows():
                item = {}
                for excel_col, model_field in column_map.items():
                    if excel_col in df.columns:
                        val = row[excel_col]
                        if pd.isna(val):
                            val = None

                        if model_field == "mesafe_km" and val:
                            try:
                                val = float(val)
                            except Exception:
                                val = 0.0

                        item[model_field] = val

                if item.get("cikis_yeri") and item.get("varis_yeri"):
                    result.append(item)
            return result
        except Exception as e:
            logger.error(f"Sync route excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {e!s}")

    @staticmethod
    async def parse_vehicle_excel(content: bytes) -> List[Dict[str, Any]]:
        """Araç Excel dosyasını (bytes) parse et."""
        import asyncio

        return await asyncio.to_thread(ExcelService._parse_vehicle_excel_sync, content)

    @staticmethod
    def _parse_vehicle_excel_sync(content: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            column_map = SafeColumnMapper.map_columns(df.columns.tolist())
            logger.info(f"Vehicle Excel Map: {column_map}")

            result = []
            for index, row in df.iterrows():
                try:

                    def safe_float(v, default=0.0):
                        try:
                            return float(v) if v is not None else default
                        except Exception:
                            return default

                    def safe_int(v, default=0):
                        try:
                            return int(float(v)) if v is not None else default
                        except Exception:
                            return default

                    item = {}
                    for excel_col, model_field in column_map.items():
                        val = row[excel_col]
                        if model_field == "plaka":
                            val = str(val).upper().replace(" ", "") if val else None
                        elif model_field in ["marka", "model", "notlar"]:
                            val = str(val) if val else None
                        elif model_field in ["yil", "tank_kapasitesi"]:
                            val = safe_int(val, None if model_field == "yil" else 600)
                        elif model_field in [
                            "bos_agirlik_kg",
                            "motor_verimliligi",
                            "hedef_tuketim",
                        ]:
                            val = safe_float(
                                val, 8000.0 if "agirlik" in model_field else 0.38
                            )

                        item[model_field] = val

                    if item.get("plaka") and item.get("marka"):
                        result.append(item)
                except Exception as row_err:
                    logger.warning(f"Vehicle row {index + 2} error: {row_err}")
                    continue
            return result
        except Exception as e:
            logger.error(f"Sync vehicle excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {e!s}")

    @staticmethod
    async def parse_driver_excel(content: bytes) -> List[Dict[str, Any]]:
        """Şoför Excel dosyasını (bytes) parse et."""
        import asyncio

        return await asyncio.to_thread(ExcelService._parse_driver_excel_sync, content)

    @staticmethod
    def _parse_driver_excel_sync(content: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            column_map = SafeColumnMapper.map_columns(df.columns.tolist())
            logger.info(f"Driver Excel Map: {column_map}")

            result = []
            for index, row in df.iterrows():
                try:
                    item = {}
                    for excel_col, model_field in column_map.items():
                        val = row[excel_col]
                        if model_field == "ad_soyad":
                            val = str(val).strip().title() if val else None
                        elif model_field == "ise_baslama":
                            val = _parse_date_flexible(val)
                        elif model_field in ["telefon", "ehliyet_sinifi", "notlar"]:
                            val = str(val) if val else None

                        item[model_field] = val

                    if item.get("ad_soyad"):
                        result.append(item)
                except Exception as row_err:
                    logger.warning(f"Driver row {index + 2} error: {row_err}")
                    continue
            return result
        except Exception as e:
            logger.error(f"Sync driver excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {e!s}")

    @staticmethod
    async def parse_dorse_excel(content: bytes) -> List[Dict[str, Any]]:
        """Dorse Excel dosyasını (bytes) parse et."""
        import asyncio

        return await asyncio.to_thread(ExcelService._parse_dorse_excel_sync, content)

    @staticmethod
    def _parse_dorse_excel_sync(content: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            column_map = SafeColumnMapper.map_columns(df.columns.tolist())
            logger.info(f"Dorse Excel Map: {column_map}")

            result = []
            for index, row in df.iterrows():
                try:

                    def safe_float(v, default=0.0):
                        try:
                            return float(v) if v is not None else default
                        except Exception:
                            return default

                    def safe_int(v, default=0):
                        try:
                            return int(float(v)) if v is not None else default
                        except Exception:
                            return default

                    item = {}
                    for excel_col, model_field in column_map.items():
                        val = row[excel_col]
                        if model_field == "plaka":
                            val = str(val).upper().replace(" ", "") if val else None
                        elif model_field in ["marka", "model", "dorse_tipi", "notlar"]:
                            val = str(val) if val else None
                        elif model_field in ["yil", "lastik_sayisi"]:
                            val = safe_int(val, None)
                        elif model_field in [
                            "bos_agirlik_kg",
                            "rolling_resistance",
                            "drag_coefficient",
                        ]:
                            val = safe_float(val, 0.0)

                        item[model_field] = val

                    if item.get("plaka"):
                        result.append(item)
                except Exception as row_err:
                    logger.warning(f"Dorse row {index + 2} error: {row_err}")
                    continue
            return result
        except Exception as e:
            logger.error(f"Sync dorse excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {e!s}")

    @classmethod
    async def parse_fuel_data(cls, file: UploadFile) -> List[Dict[str, Any]]:
        """Yakıt (Fuel) Excel dosyasını parse et (UploadFile)"""
        df = await cls._read_excel_to_df(file)
        import asyncio

        return await asyncio.to_thread(cls._parse_fuel_data_sync, df)

    @classmethod
    def _parse_fuel_data_sync(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        column_map = SafeColumnMapper.map_columns(df.columns.tolist())
        logger.info(f"Fuel Data Map: {column_map}")

        required_internal = ["tarih", "plaka", "litre"]
        found_internal = list(column_map.values())

        missing = [r for r in required_internal if r not in found_internal]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Eksik sütunlar (veya anlaşılamadı): {', '.join(missing)}",
            )

        result = []
        for index, row in df.iterrows():
            try:
                # Safe casting logic
                def safe_float(v, default=0.0):
                    try:
                        return float(v) if v is not None else default
                    except Exception:
                        return default

                def safe_int(v, default=0):
                    try:
                        return int(float(v)) if v is not None else default
                    except Exception:
                        return default

                data = {}
                for excel_col, model_field in column_map.items():
                    val = row[excel_col]
                    if model_field == "tarih":
                        val = _parse_date_flexible(val)
                    elif model_field == "plaka":
                        val = str(val).upper().replace(" ", "") if val else None
                    elif model_field == "litre":
                        val = safe_float(val)
                    elif model_field in ["toplam_tutar", "fiyat_tl"]:
                        val = safe_float(val)
                    elif model_field == "km_sayac":
                        val = safe_int(val)

                    data[model_field] = val

                # Recalculate prices if missing
                litre = data.get("litre", 0)
                tutar = data.get("toplam_tutar", 0)
                fiyat = data.get("fiyat_tl", 0)

                if litre > 0:
                    if tutar > 0 and fiyat == 0:
                        data["fiyat_tl"] = round(tutar / litre, 2)
                    elif fiyat > 0 and tutar == 0:
                        data["toplam_tutar"] = round(fiyat * litre, 2)

                result.append(data)

                result.append(data)
            except Exception as e:
                logger.warning(f"Excel row {index + 2} parse error: {e}")
                # İlerlemeye devam ediyoruz, hata fırlatmıyoruz (veya listeye hata ekleyebiliriz)
                continue
        return result

    @classmethod
    async def parse_trip_data(cls, file: UploadFile) -> List[Dict[str, Any]]:
        """Sefer (Trip) Excel dosyasını parse et (UploadFile)"""
        df = await cls._read_excel_to_df(file)
        import asyncio

        return await asyncio.to_thread(cls._parse_trip_data_sync, df)

    @classmethod
    def _parse_trip_data_sync(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        required_cols = ["tarih", "sofor", "plaka", "cikis", "varis"]
        # Alias handling for some columns
        if "sofor_ad" in df.columns and "sofor" not in df.columns:
            df["sofor"] = df["sofor_ad"]
        if "soforadi" in df.columns and "sofor" not in df.columns:
            df["sofor"] = df["soforadi"]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, detail=f"Eksik sütunlar: {', '.join(missing_cols)}"
            )

        result = []
        for index, row in df.iterrows():
            try:

                def safe_float(v, default=0.0):
                    try:
                        return float(v) if v is not None else default
                    except Exception:
                        return default

                def safe_int(v, default=0):
                    try:
                        return int(float(v)) if v is not None else default
                    except Exception:
                        return default

                data = {
                    "tarih": _parse_date_flexible(row.get("tarih")),
                    "sofor_ad": str(row.get("sofor")),
                    "plaka": str(row.get("plaka")).upper()
                    if row.get("plaka")
                    else None,
                    "dorse_plakasi": str(row.get("dorse_plakasi")).upper()
                    if row.get("dorse_plakasi")
                    else None,
                    "cikis_yeri": str(row.get("cikis")),
                    "varis_yeri": str(row.get("varis")),
                    "mesafe_km": safe_int(row.get("km") or row.get("mesafe_km")),
                    "ton": safe_float(
                        row.get("ton") or row.get("net_kg") or row.get("yukkg")
                    ),
                    "saat": str(row.get("saat")) if row.get("saat") else None,
                    "durum": str(row.get("durum")) if row.get("durum") else "Tamam",
                }
                result.append(data)
            except Exception as e:
                logger.warning(f"Excel row {index + 2} parse error: {e}")
                continue
        return result

    @classmethod
    async def parse_vehicle_data(cls, file: UploadFile) -> List[Dict[str, Any]]:
        """Araç verilerini parse et (Async & Non-blocking)"""
        df = await cls._read_excel_to_df(file)
        import asyncio

        return await asyncio.to_thread(cls._parse_vehicle_data_sync, df)

    @classmethod
    def _parse_vehicle_data_sync(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        required = ["plaka", "marka"]
        for col in required:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Eksik kolon: {col}")

        result = []
        for index, row in df.iterrows():
            try:

                def safe_float(v, default=0.0):
                    try:
                        return float(v) if v is not None else default
                    except Exception:
                        return default

                def safe_int(v, default=0):
                    try:
                        return int(float(v)) if v is not None else default
                    except Exception:
                        return default

                result.append(
                    {
                        "plaka": str(row.get("plaka")).upper()
                        if row.get("plaka")
                        else None,
                        "marka": str(row.get("marka")),
                        "model": str(row.get("model")) if row.get("model") else None,
                        "yil": safe_int(row.get("yil"), None),
                        "tank_kapasitesi": safe_int(row.get("tank_kapasitesi"), 600),
                        "bos_agirlik_kg": safe_float(row.get("bos_agirlik_kg"), 8000.0),
                        "motor_verimliligi": safe_float(
                            row.get("motor_verimliligi") or row.get("motor"), 0.38
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"Excel row {index + 2} parse error: {e}")
                continue
        return result

    @classmethod
    async def parse_driver_data(cls, file: UploadFile) -> List[Dict[str, Any]]:
        """Şoför verilerini parse et (Async & Non-blocking)"""
        df = await cls._read_excel_to_df(file)
        import asyncio

        return await asyncio.to_thread(cls._parse_driver_data_sync, df)

    @classmethod
    def _parse_driver_data_sync(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if "ad_soyad" not in df.columns and "sofor" not in df.columns:
            raise HTTPException(
                status_code=400, detail="Eksik kolon: ad_soyad veya sofor"
            )

        name_col = "ad_soyad" if "ad_soyad" in df.columns else "sofor"

        result = []
        for index, row in df.iterrows():
            try:
                result.append(
                    {
                        "ad_soyad": str(row.get(name_col)),
                        "telefon": str(row.get("telefon"))
                        if row.get("telefon")
                        else None,
                        "ise_baslama": _parse_date_flexible(
                            row.get("ise_baslama") or row.get("tarih")
                        ),
                        "ehliyet_sinifi": str(
                            row.get("ehliyet_sinifi") or row.get("ehliyet") or "E"
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"Excel row {index + 2} parse error: {e}")
                continue
        return result

    # =========================================================================
    # TEMPLATE GENERATOR
    # =========================================================================

    @staticmethod
    def generate_template(type: str) -> bytes:
        """Şablon Excel dosyası oluşturur"""
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine="xlsxwriter")

        if type == "sefer":
            columns = [
                "Tarih",
                "Saat",
                "Çıkış Yeri",
                "Varış Yeri",
                "Mesafe (KM)",
                "Yük (KG)",
                "Plaka",
                "Dorse Plakası",
                "Şoför Adı",
                "Durum",
            ]
            data = [
                [
                    "2025-01-01",
                    "09:00",
                    "Istanbul",
                    "Ankara",
                    450,
                    15000,
                    "34ABC01",
                    "34XYZ99",
                    "Ahmet Yilmaz",
                    "Tamam",
                ],
                [
                    "YYYY-MM-DD",
                    "HH:MM",
                    "Text",
                    "Text",
                    "Number",
                    "Number",
                    "Text",
                    "Text",
                    "Text",
                    "Tamam/Bekliyor/Iptal",
                ],
            ]
        elif type == "yakit":
            columns = [
                "Tarih",
                "Plaka",
                "İstasyon",
                "Fiyat",
                "Litre",
                "KM",
                "Fiş No",
                "Depo Durumu",
            ]
            data = [
                [
                    "2025-02-10",
                    "34 ABC 123",
                    "Shell Maslak",
                    42.50,
                    500,
                    120500,
                    "FIS-001",
                    "Doldu",
                ],
                [
                    "YYYY-MM-DD",
                    "Text",
                    "Text",
                    "Number",
                    "Number",
                    "Number",
                    "Text",
                    "Doldu/Kısmi",
                ],
            ]
        elif type == "arac":
            columns = [
                "Plaka",
                "Marka",
                "Model",
                "Yil",
                "Tank_Kapasitesi",
                "Bos_Agirlik_KG",
                "Motor_Verimliligi",
            ]
            data = [["34ABC01", "Mercedes", "Actros", 2022, 600, 8200, 0.38]]
        elif type == "sofor":
            columns = ["Ad_Soyad", "Telefon", "Ise_Baslama", "Ehliyet_Sinifi"]
            data = [["Ahmet Yilmaz", "5551234567", "2023-01-01", "CE"]]
        elif type == "guzergah":
            columns = [
                "Çıkış Yeri",
                "Varış Yeri",
                "Mesafe (KM)",
                "Notlar",
            ]
            data = [
                [
                    "Istanbul",
                    "Ankara",
                    450,
                    "Standart Rota",
                ],
                [
                    "Text",
                    "Text",
                    "Number",
                    "Number",
                    "Text",
                ],
            ]
        elif type == "dorse":
            columns = [
                "Plaka",
                "Marka",
                "Model",
                "Yil",
                "Dorse_Tipi",
                "Bos_Agirlik_KG",
                "Lastik_Sayisi",
                "Rolling_Resistance",
                "Drag_Coefficient",
            ]
            data = [
                ["34XYZ99", "Tirsan", "Frigo", 2023, "Tenteli", 7200, 6, 0.006, 0.75]
            ]
        else:
            return b""

        df = pd.DataFrame(data, columns=columns)
        df.to_excel(writer, index=False, sheet_name="Sablon")

        # Sütun genişliklerini ayarla
        worksheet = writer.sheets["Sablon"]
        for i, col in enumerate(columns):
            worksheet.set_column(i, i, 20)

        writer.close()
        return output.getvalue()

    # =========================================================================
    # DATA EXPORT ENGINE (Phase 2 - Advanced Export)
    # =========================================================================

    @staticmethod
    def export_data(data: List[Dict[str, Any]], type: str = "generic") -> bytes:
        """
        Verilen veri listesini kurumsal formatta Excel'e çevirir.
        LojiNext Design System renkleri ve profesyonel formatlama uygulanır.
        """
        if not data:
            # Boş veri için boş bir Excel döndür
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data)

        # Tip bazlı kolon başlıkları ve sıralama (Opsiyonel)
        if type == "arac_listesi":
            # Map columns for Turkish report
            df = df.rename(
                columns={
                    "plaka": "Plaka",
                    "marka": "Marka",
                    "model": "Model",
                    "yil": "Model Yılı",
                    "tank_kapasitesi": "Tank Kapasitesi (LT)",
                    "bos_agirlik_kg": "Boş Ağırlık (KG)",
                    "motor_verimliligi": "Motor Verimliliği",
                }
            )
        elif type == "dorse_listesi":
            df = df.rename(
                columns={
                    "plaka": "Plaka",
                    "marka": "Marka",
                    "model": "Model",
                    "yil": "Model Yılı",
                    "dorse_tipi": "Dorse Tipi",
                    "bos_agirlik_kg": "Boş Ağırlık (KG)",
                    "lastik_sayisi": "Lastik Sayısı",
                    "aktif": "Durum",
                }
            )
            if "Durum" in df.columns:
                df["Durum"] = df["Durum"].map({True: "Aktif", False: "Pasif"})
        elif type == "sefer_listesi":
            # Map columns for Turkish report
            df = df.rename(
                columns={
                    "tarih": "Tarih",
                    "saat": "Saat",
                    "cikis_yeri": "Çıkış Yeri",
                    "varis_yeri": "Varış Yeri",
                    "mesafe_km": "Mesafe (KM)",
                    "net_kg": "Yük (KG)",
                    "plaka": "Plaka",
                    "sofor": "Şoför",
                    "durum": "Durum",
                    "tahmini_yakit_lt": "Tahm. Yakıt (LT)",
                }
            )
            # Filter only useful columns if any exist
            cols = [
                "Tarih",
                "Saat",
                "Çıkış Yeri",
                "Varış Yeri",
                "Mesafe (KM)",
                "Yük (KG)",
                "Plaka",
                "Şoför",
                "Durum",
                "Tahm. Yakıt (LT)",
            ]
            df = df[[c for c in cols if c in df.columns]]
        elif type == "yakit_listesi":
            # Map columns for Turkish report
            df = df.rename(
                columns={
                    "tarih": "Tarih",
                    "plaka": "Plaka",
                    "istasyon": "İstasyon",
                    "fiyat_tl": "Birim Fiyat (TL)",
                    "litre": "Litre",
                    "km_sayac": "KM Sayacı",
                    "fis_no": "Fiş No",
                    "toplam_tutar": "Toplam Tutar (TL)",
                    "depo_durumu": "Depo Durumu",
                }
            )
            cols = [
                "Tarih",
                "Plaka",
                "İstasyon",
                "Birim Fiyat (TL)",
                "Litre",
                "Toplam Tutar (TL)",
                "KM Sayacı",
                "Fiş No",
                "Depo Durumu",
            ]
            df = df[[c for c in cols if c in df.columns]]
        elif type == "lokasyon_listesi":
            df = df.rename(
                columns={
                    "cikis_yeri": "Çıkış Yeri",
                    "varis_yeri": "Varış Yeri",
                    "mesafe_km": "Mesafe (KM)",
                    "tahmini_sure_saat": "Tahmini Süre (Saat)",
                    "zorluk": "Zorluk",
                    "otoban_mesafe_km": "Otoban (KM)",
                    "sehir_ici_mesafe_km": "Şehiriçi (KM)",
                    "flat_distance_km": "Düz Yol (KM)",
                    "notlar": "Notlar",
                    "aktif": "Durum",
                }
            )
            cols = [
                "Çıkış Yeri",
                "Varış Yeri",
                "Mesafe (KM)",
                "Tahmini Süre (Saat)",
                "Zorluk",
                "Otoban (KM)",
                "Şehiriçi (KM)",
                "Düz Yol (KM)",
                "Durum",
                "Notlar",
            ]
            df = df[[c for c in cols if c in df.columns]]
            # Durum kolonunu True/False yerine Aktif/Pasif yapalım
            if "Durum" in df.columns:
                df["Durum"] = df["Durum"].map({True: "Aktif", False: "Pasif"})
        else:
            # Kolon isimlerini baş harfi büyük yap ve alt çizgileri boşluğa çevir
            df.columns = [str(c).replace("_", " ").title() for c in df.columns]

        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine="xlsxwriter")
        sheet_name = "Rapor"

        df.to_excel(
            writer, index=False, sheet_name=sheet_name, startrow=1
        )  # Başlık için 1 satır boşluk

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # ---------------------------------------------------------------------
        # LOJINEXT STYLING
        # ---------------------------------------------------------------------

        # Renk Paleti
        PRIMARY_COLOR = "#3B82F6"  # Blue 500
        HEADER_BG = "#1E293B"  # Slate 800
        HEADER_TEXT = "#FFFFFF"  # White
        BORDER_COLOR = "#CBD5E1"  # Slate 300

        # Formatlar
        header_format = workbook.add_format(
            {
                "bold": True,
                "text_wrap": False,
                "valign": "vcenter",
                "fg_color": HEADER_BG,
                "font_color": HEADER_TEXT,
                "border": 1,
                "border_color": BORDER_COLOR,
                "font_size": 11,
                "font_name": "Calibri",
            }
        )

        cell_format = workbook.add_format(
            {
                "border": 1,
                "border_color": BORDER_COLOR,
                "valign": "vcenter",
                "font_size": 10,
                "font_name": "Calibri",
            }
        )

        date_format = workbook.add_format(
            {
                "border": 1,
                "border_color": BORDER_COLOR,
                "num_format": "dd.mm.yyyy",
                "valign": "vcenter",
                "font_size": 10,
                "font_name": "Calibri",
            }
        )

        number_format = workbook.add_format(
            {
                "border": 1,
                "border_color": BORDER_COLOR,
                "num_format": "#,##0.00",
                "valign": "vcenter",
                "font_size": 10,
                "font_name": "Calibri",
            }
        )

        title_format = workbook.add_format(
            {
                "bold": True,
                "font_size": 14,
                "font_name": "Calibri",
                "font_color": PRIMARY_COLOR,
            }
        )

        # ---------------------------------------------------------------------
        # UYGULAMA
        # ---------------------------------------------------------------------

        # Rapor Başlığı
        title = f"{type.upper()} RAPORU - {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')}"
        worksheet.write(0, 0, title, title_format)

        # Kolon Başlıklarını Elle Yaz (Pandas'ınkini eziyoruz stil için)
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(1, col_num, value, header_format)

        # Veri Satırları
        if not df.empty:
            for row_num, row_data in enumerate(df.values):
                for col_num, cell_value in enumerate(row_data):
                    # Format belirle
                    fmt = cell_format

                    if isinstance(cell_value, (date, datetime, pd.Timestamp)):
                        fmt = date_format
                    elif isinstance(cell_value, (int, float)):
                        fmt = number_format

                    worksheet.write(row_num + 2, col_num, cell_value, fmt)

            # Sütun Genişliklerini Otomatik Ayarla
            for i, col in enumerate(df.columns):
                # Başlık uzunluğu
                max_len = len(str(col)) + 4

                # Veri uzunluğu (ilk 50 satırı kontrol et performans için)
                column_data = df.iloc[:50, i]
                for val in column_data:
                    if val is not None:
                        max_len = max(max_len, len(str(val)))

                # Limitler
                max_len = min(max_len, 50)  # Max 50 char
                worksheet.set_column(i, i, max_len)

        # Auto-Filter Ekle
        if not df.empty:
            (max_row, max_col) = df.shape
            worksheet.autofilter(1, 0, max_row + 1, max_col - 1)

        writer.close()
        return output.getvalue()
