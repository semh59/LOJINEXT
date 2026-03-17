"""
Araç (Vehicle) Pydantic şemaları.

Güvenlik kontrolleri:
- Plaka format regex validasyonu
- String length constraints
- XSS/injection koruması
- Null byte sanitizasyonu
"""

from datetime import date, datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import sanitize_string, validate_safe_string


class AracBase(BaseModel):
    """Araç base model - ortak alanlar."""

    plaka: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[0-9]{2}[\s-]?[A-ZÇĞİÖŞÜ]{1,5}[\s-]?[0-9]{2,4}$",
        description="Plaka formatı (Permissive)",
    )
    marka: str = Field(..., min_length=2, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    yil: Optional[int] = Field(None, ge=1990, description="Üretim yılı")
    tank_kapasitesi: int = Field(
        600, gt=0, le=5000, description="Tank kapasitesi (litre)"
    )
    hedef_tuketim: float = Field(
        32.0, gt=0, le=100, description="Hedef tüketim (lt/100km)"
    )

    # Araç Teknik Özellikleri (Aerodinamik)
    bos_agirlik_kg: float = Field(
        8000.0, gt=0, le=40000, description="Boş Ağırlık (kg)"
    )
    hava_direnc_katsayisi: float = Field(
        0.7, gt=0.1, le=2.0, description="Hava Direnç Katsayısı (Cd)"
    )
    on_kesit_alani_m2: float = Field(
        8.5, gt=1.0, le=20.0, description="Ön Kesit Alanı (m2)"
    )
    motor_verimliligi: float = Field(
        0.38, gt=0.1, le=1.0, description="Motor Verimliliği (0-1 arası)"
    )
    lastik_direnc_katsayisi: float = Field(
        0.007, gt=0.001, le=0.1, description="Lastik Direnç Katsayısı (Crr)"
    )
    maks_yuk_kapasitesi_kg: int = Field(
        26000, gt=0, le=50000, description="Maksimum Yük Kapasitesi (kg)"
    )

    aktif: bool = True
    muayene_tarihi: Optional[date] = Field(
        None, description="Muayene Geçerlilik Tarihi"
    )
    notlar: Optional[str] = Field(None, max_length=500)

    @field_validator("yil")
    @classmethod
    def check_yil(cls, v: Optional[int]) -> Optional[int]:
        """Yıl kontrolü - gelecek yıl + 1'den büyük olamaz."""
        if v is None:
            return v
        current_year = datetime.now(timezone.utc).year
        if v > current_year + 1:
            raise ValueError(f"Yıl {current_year + 1} değerinden büyük olamaz")
        return v

    @field_validator("plaka", mode="before")
    @classmethod
    def sanitize_plaka(cls, v: Optional[str]) -> Optional[str]:
        """Plaka whitespace strip."""
        return sanitize_string(v) if isinstance(v, str) else v

    @field_validator("marka", "model", mode="before")
    @classmethod
    def validate_marka_model(cls, v: Optional[str]) -> Optional[str]:
        """Marka ve model XSS koruması."""
        return validate_safe_string(v)

    @field_validator("notlar", mode="before")
    @classmethod
    def validate_notlar(cls, v: Optional[str]) -> Optional[str]:
        """Notlar alanı XSS koruması."""
        return validate_safe_string(v)


class AracCreate(AracBase):
    """Araç oluşturma şeması."""

    pass


class AracUpdate(BaseModel):
    """Araç güncelleme şeması - tüm alanlar optional."""

    plaka: Optional[str] = Field(
        None,
        min_length=3,
        max_length=20,
        pattern=r"^[0-9]{2}[\s-]?[A-ZÇĞİÖŞÜ]{1,5}[\s-]?[0-9]{2,4}$",
    )
    marka: Optional[str] = Field(None, min_length=2, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    yil: Optional[int] = Field(None, ge=1990)
    tank_kapasitesi: Optional[int] = Field(None, gt=0, le=5000)
    hedef_tuketim: Optional[float] = Field(None, gt=0, le=100)
    bos_agirlik_kg: Optional[float] = Field(None, gt=0, le=40000)
    hava_direnc_katsayisi: Optional[float] = Field(None, gt=0.1, le=2.0)
    on_kesit_alani_m2: Optional[float] = Field(None, gt=1.0, le=20.0)
    motor_verimliligi: Optional[float] = Field(
        None, gt=0.1, le=1.0, description="Motor Verimliliği (0-1 arası)"
    )
    lastik_direnc_katsayisi: Optional[float] = Field(
        None, gt=0.001, le=0.1, description="Lastik Direnç Katsayısı (Crr)"
    )
    maks_yuk_kapasitesi_kg: Optional[int] = Field(
        None, gt=0, le=50000, description="Maksimum Yük Kapasitesi (kg)"
    )
    aktif: Optional[bool] = None
    muayene_tarihi: Optional[date] = Field(
        None, description="Muayene Geçerlilik Tarihi"
    )
    notlar: Optional[str] = Field(None, max_length=500)

    @field_validator("yil")
    @classmethod
    def check_yil(cls, v: Optional[int]) -> Optional[int]:
        """Yıl kontrolü."""
        if v is None:
            return v
        current_year = datetime.now(timezone.utc).year
        if v > current_year + 1:
            raise ValueError(f"Yıl {current_year + 1} değerinden büyük olamaz")
        return v

    @field_validator("plaka", mode="before")
    @classmethod
    def sanitize_plaka(cls, v: Optional[str]) -> Optional[str]:
        """Plaka whitespace strip."""
        return sanitize_string(v) if isinstance(v, str) else v

    @field_validator("marka", "model", mode="before")
    @classmethod
    def validate_marka_model(cls, v: Optional[str]) -> Optional[str]:
        """Marka ve model XSS koruması."""
        return validate_safe_string(v)

    @field_validator("notlar", mode="before")
    @classmethod
    def validate_notlar(cls, v: Optional[str]) -> Optional[str]:
        """Notlar alanı XSS koruması."""
        return validate_safe_string(v)


class AracResponse(AracBase):
    """
    Araç response şeması - API çıktısı.

    [HEALING] Bozuk verileri otomatik düzeltir veya sessizce kabul eder
    böylece liste görünümünü bozmaz.
    """

    id: int
    plaka: str = Field(
        ..., description="Türkiye plaka formatı (Permissive in response)"
    )
    created_at: datetime
    # Stats from Relation
    toplam_km: float = 0.0
    toplam_sefer: int = 0
    ort_tuketim: float = 0.0

    @field_validator("plaka", mode="before")
    @classmethod
    def heal_plaka(cls, v: Any) -> str:
        """Geçersiz plaka formatını bile kabul eder (Görünürlük için)"""
        if not v:
            return "BİLİNMİYOR"
        return str(v).strip().upper()

    @field_validator("yil", mode="before")
    @classmethod
    def heal_yil(cls, v: Any) -> Optional[int]:
        """Geçersiz yılları null'a çeker, hata fırlatmaz"""
        if v is None:
            return None
        try:
            val = int(v)
            if val < 1900 or val > 2100:
                return None
            return val
        except (ValueError, TypeError):
            return None

    model_config = ConfigDict(from_attributes=True)
