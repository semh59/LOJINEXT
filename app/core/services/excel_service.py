"""
TIR Yakıt Takip - Konsolide Excel Servisi
Sefer, Yakıt, Araç ve Şoför Excel dosyalarını işler, şablon oluşturur.
"""

import io
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

# Desteklenen tarih formatları (multi-locale support)
DATE_FORMATS = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"]


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
                status_code=400, detail=f"Excel dosyası okunamadı veya bozuk: {str(e)}"
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
            column_map = {
                "Tarih": "tarih",
                "Saat": "saat",
                "CikisYeri": "cikis_yeri",
                "VarisYeri": "varis_yeri",
                "MesafeKM": "mesafe_km",
                "YukKG": "net_kg",
                "Plaka": "plaka",
                "SoforAdi": "sofor_adi",
            }
            df.columns = [str(c).strip() for c in df.columns]

            result = []
            for _, row in df.iterrows():
                item = {}
                for excel_col, model_field in column_map.items():
                    if excel_col in df.columns:
                        val = row[excel_col]
                        if model_field == "tarih":
                            val = _parse_date_flexible(val)
                        if pd.isna(val):
                            val = None

                        # FAZ 2.2: Güvenli tip dönüşümü (Safe Cast)
                        if model_field == "mesafe_km" and val:
                            try:
                                val = int(float(val))
                            except:
                                val = 0
                        if model_field == "net_kg" and val:
                            try:
                                val = float(val)
                            except:
                                val = 0.0

                        item[model_field] = val
                result.append(item)
            return result
        except Exception as e:
            logger.error(f"Sync sefer excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {str(e)}")

    @staticmethod
    async def parse_yakit_excel(content: bytes) -> List[Dict[str, Any]]:
        """Yakıt Excel dosyasını (bytes) parse et (Async & Non-blocking)."""
        import asyncio

        return await asyncio.to_thread(ExcelService._parse_yakit_excel_sync, content)

    @staticmethod
    def _parse_yakit_excel_sync(content: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            column_map = {
                "Tarih": "tarih",
                "Plaka": "plaka",
                "Istasyon": "istasyon",
                "Fiyat": "fiyat_tl",
                "Litre": "litre",
                "KM": "km_sayac",
                "FisNo": "fis_no",
            }
            df.columns = [str(c).strip() for c in df.columns]

            result = []
            for _, row in df.iterrows():
                item = {}
                for excel_col, model_field in column_map.items():
                    if excel_col in df.columns:
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
                result.append(item)
            return result
        except Exception as e:
            logger.error(f"Sync yakit excel error: {e}")
            raise ValueError(f"Excel okuma hatası: {str(e)}")

    # =========================================================================
    # API PARSING (UploadFile based - used by Endpoints)
    # =========================================================================

    @classmethod
    async def parse_fuel_data(cls, file: UploadFile) -> List[Dict[str, Any]]:
        """Yakıt (Fuel) Excel dosyasını parse et (UploadFile)"""
        df = await cls._read_excel_to_df(file)
        import asyncio

        return await asyncio.to_thread(cls._parse_fuel_data_sync, df)

    @classmethod
    def _parse_fuel_data_sync(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        required_cols = ["tarih", "plaka", "litre"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if (
            "tutar" not in df.columns
            and "fiyat" not in df.columns
            and "toplam_tutar" not in df.columns
        ):
            missing_cols.append("tutar/fiyat")

        if missing_cols:
            raise HTTPException(
                status_code=400, detail=f"Eksik sütunlar: {', '.join(missing_cols)}"
            )

        result = []
        for index, row in df.iterrows():
            try:
                # Safe casting logic
                def safe_float(v, default=0.0):
                    try:
                        return float(v) if v is not None else default
                    except:
                        return default

                def safe_int(v, default=0):
                    try:
                        return int(float(v)) if v is not None else default
                    except:
                        return default

                data = {
                    "tarih": _parse_date_flexible(row.get("tarih")),
                    "plaka": str(row.get("plaka")).upper() if row.get("plaka") else None,
                    "litre": safe_float(row.get("litre")),
                    "toplam_tutar": safe_float(row.get("tutar") or row.get("toplam_tutar")),
                    "fiyat_tl": safe_float(row.get("fiyat") or row.get("fiyat_tl")),
                    "km_sayac": safe_int(row.get("km") or row.get("km_sayac")),
                    "istasyon": row.get("istasyon") or "Bilinmiyor",
                    "fis_no": str(row.get("fis_no")) if row.get("fis_no") else None,
                    "depo_durumu": str(row.get("depo_durumu"))
                    if row.get("depo_durumu")
                    else "Bilinmiyor",
                }

                if data["litre"] > 0:
                    if data["toplam_tutar"] > 0 and data["fiyat_tl"] == 0:
                        data["fiyat_tl"] = round(data["toplam_tutar"] / data["litre"], 2)
                    elif data["fiyat_tl"] > 0 and data["toplam_tutar"] == 0:
                        data["toplam_tutar"] = round(data["fiyat_tl"] * data["litre"], 2)

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
                    except:
                        return default

                def safe_int(v, default=0):
                    try:
                        return int(float(v)) if v is not None else default
                    except:
                        return default

                data = {
                    "tarih": _parse_date_flexible(row.get("tarih")),
                    "sofor_ad": str(row.get("sofor")),
                    "plaka": str(row.get("plaka")).upper() if row.get("plaka") else None,
                    "cikis_yeri": str(row.get("cikis")),
                    "varis_yeri": str(row.get("varis")),
                    "mesafe_km": safe_int(row.get("km") or row.get("mesafe_km")),
                    "ton": safe_float(row.get("ton") or row.get("net_kg") or row.get("yukkg")),
                    "saat": str(row.get("saat")) if row.get("saat") else None,
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
                    except:
                        return default

                def safe_int(v, default=0):
                    try:
                        return int(float(v)) if v is not None else default
                    except:
                        return default

                result.append(
                    {
                        "plaka": str(row.get("plaka")).upper() if row.get("plaka") else None,
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
            raise HTTPException(status_code=400, detail=f"Eksik kolon: ad_soyad veya sofor")

        name_col = "ad_soyad" if "ad_soyad" in df.columns else "sofor"

        result = []
        for index, row in df.iterrows():
            try:
                result.append(
                    {
                        "ad_soyad": str(row.get(name_col)),
                        "telefon": str(row.get("telefon")) if row.get("telefon") else None,
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
                "CikisYeri",
                "VarisYeri",
                "MesafeKM",
                "YukKG",
                "Plaka",
                "SoforAdi",
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
                    "Ahmet Yilmaz",
                ],
                ["YYYY-MM-DD", "HH:MM", "Text", "Text", "Number", "Number", "Text", "Text"],
            ]
        elif type == "yakit":
            columns = ["Tarih", "Plaka", "Istasyon", "Fiyat", "Litre", "KM", "FisNo"]
            data = [
                ["2025-01-01", "34ABC01", "Shell Gebze", 42.50, 500, 120500, "FIS123"],
                ["YYYY-MM-DD", "Text", "Text", "Number", "Number", "Number", "Text"],
            ]
        elif type == "arac":
            columns = ["Plaka", "Marka", "Model", "Yil", "Tank_Kapasitesi", "Bos_Agirlik_KG", "Motor_Verimliligi"]
            data = [["34ABC01", "Mercedes", "Actros", 2022, 600, 8200, 0.38]]
        elif type == "sofor":
            columns = ["Ad_Soyad", "Telefon", "Ise_Baslama", "Ehliyet_Sinifi"]
            data = [["Ahmet Yilmaz", "5551234567", "2023-01-01", "CE"]]
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
        # Eğer özel mapping gerekirse burada yapılabilir.
        # Şimdilik DataFrame kolonlarını temizleyip kullanıyoruz.
        
        # Kolon isimlerini baş harfi büyük yap ve alt çizgileri boşluğa çevir
        df.columns = [str(c).replace("_", " ").title() for c in df.columns]

        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine="xlsxwriter")
        sheet_name = "Rapor"
        
        df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=1) # Başlık için 1 satır boşluk

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # ---------------------------------------------------------------------
        # LOJINEXT STYLING
        # ---------------------------------------------------------------------
        
        # Renk Paleti
        PRIMARY_COLOR = "#3B82F6"  # Blue 500
        HEADER_BG = "#1E293B"      # Slate 800
        HEADER_TEXT = "#FFFFFF"    # White
        BORDER_COLOR = "#CBD5E1"   # Slate 300
        ROW_ODD = "#F8FAFC"        # Slate 50
        ROW_EVEN = "#FFFFFF"       # White

        # Formatlar
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': False,
            'valign': 'vcenter',
            'fg_color': HEADER_BG,
            'font_color': HEADER_TEXT,
            'border': 1,
            'border_color': BORDER_COLOR,
            'font_size': 11,
            'font_name': 'Calibri'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'border_color': BORDER_COLOR,
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Calibri'
        })
        
        date_format = workbook.add_format({
            'border': 1,
            'border_color': BORDER_COLOR,
            'num_format': 'dd.mm.yyyy',
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Calibri'
        })

        number_format = workbook.add_format({
            'border': 1,
            'border_color': BORDER_COLOR,
            'num_format': '#,##0.00',
            'valign': 'vcenter',
            'font_size': 10,
            'font_name': 'Calibri'
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'font_name': 'Calibri',
            'font_color': PRIMARY_COLOR
        })

        # ---------------------------------------------------------------------
        # UYGULAMA
        # ---------------------------------------------------------------------

        # Rapor Başlığı
        title = f"{type.upper()} RAPORU - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
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
                max_len = min(max_len, 50) # Max 50 char
                worksheet.set_column(i, i, max_len)

        # Auto-Filter Ekle
        if not df.empty:
            (max_row, max_col) = df.shape
            worksheet.autofilter(1, 0, max_row + 1, max_col - 1)

        writer.close()
        return output.getvalue()
