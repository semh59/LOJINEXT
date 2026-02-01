"""
Sefer (Trip) Pydantic şemaları.

Güvenlik kontrolleri:
- XSS koruması (çıkış/varış yerleri)
- String sanitizasyonu
- Numeric constraints
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import sanitize_string, validate_safe_string


class SeferBase(BaseModel):
    """Sefer base model - ortak alanlar."""
    
    tarih: date
    saat: Optional[str] = Field(
        None, 
        pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="HH:mm formatı"
    )
    arac_id: int = Field(..., gt=0)
    sofor_id: int = Field(..., gt=0)
    guzergah_id: int = Field(..., gt=0, description="Güzergah seçimi zorunlu")
    
    # Weight Info
    bos_agirlik_kg: int = Field(0, ge=0)
    dolu_agirlik_kg: int = Field(0, ge=0)
    net_kg: int = Field(0, ge=0)
    ton: float = Field(0.0, ge=0.0)
    
    # Location
    cikis_yeri: str = Field(..., min_length=1, max_length=100)
    varis_yeri: str = Field(..., min_length=1, max_length=100)
    mesafe_km: int = Field(..., gt=0, le=10000)
    baslangic_km: Optional[int] = Field(None, ge=0, le=9999999)
    bitis_km: Optional[int] = Field(None, ge=0, le=9999999)
    
    bos_sefer: bool = False
    durum: Literal["Tamam", "Devam Ediyor", "İptal", "Planlandı", "Yolda", "Bekliyor"] = Field("Tamam")
    dagitilan_yakit: Optional[Decimal] = Field(None, ge=0, le=10000)
    tuketim: Optional[float] = Field(None, ge=0, le=1000)
    ascent_m: Optional[float] = Field(None, ge=0, le=50000)
    descent_m: Optional[float] = Field(None, ge=0, le=50000)
    notlar: Optional[str] = Field(None, max_length=255)
    
    @field_validator('cikis_yeri', 'varis_yeri', mode='before')
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        """Lokasyon alanları XSS koruması."""
        return validate_safe_string(v)
    
    @field_validator('bitis_km')
    @classmethod
    def validate_km_range(cls, v: Optional[int], info) -> Optional[int]:
        """Bitiş km başlangıç'tan büyük olmalı."""
        if v is None:
            return v
        baslangic = info.data.get('baslangic_km')
        if baslangic is not None and v < baslangic:
            raise ValueError("Bitiş km, başlangıç km'den büyük olmalı")
        return v


class SeferCreate(SeferBase):
    """Sefer oluşturma şeması."""
    pass


class SeferUpdate(BaseModel):
    """Sefer güncelleme şeması - tüm alanlar optional."""
    
    tarih: Optional[date] = None
    saat: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    arac_id: Optional[int] = Field(None, gt=0)
    sofor_id: Optional[int] = Field(None, gt=0)
    guzergah_id: Optional[int] = Field(None, gt=0)
    
    bos_agirlik_kg: Optional[int] = Field(None, ge=0)
    dolu_agirlik_kg: Optional[int] = Field(None, ge=0)
    net_kg: Optional[int] = Field(None, ge=0)
    ton: Optional[float] = Field(None, ge=0.0)
    
    cikis_yeri: Optional[str] = Field(None, min_length=1, max_length=100)
    varis_yeri: Optional[str] = Field(None, min_length=1, max_length=100)
    mesafe_km: Optional[int] = Field(None, gt=0)
    baslangic_km: Optional[int] = Field(None, ge=0)
    bitis_km: Optional[int] = Field(None, ge=0)
    
    bos_sefer: Optional[bool] = None
    durum: Optional[Literal["Tamam", "Devam Ediyor", "İptal", "Planlandı", "Yolda", "Bekliyor"]] = None
    dagitilan_yakit: Optional[Decimal] = Field(None, ge=0)
    tuketim: Optional[float] = Field(None, ge=0)
    ascent_m: Optional[float] = Field(None, ge=0)
    descent_m: Optional[float] = Field(None, ge=0)
    notlar: Optional[str] = Field(None, max_length=255)

    @field_validator('cikis_yeri', 'varis_yeri', mode='before')
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        """Lokasyon alanları XSS koruması."""
        return validate_safe_string(v)


class SeferResponse(SeferBase):
    """
    Sefer response şeması - API çıktısı.
    """
    
    id: int
    plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    saat: Optional[str] = Field(None, description="HH:mm formatı (Permissive in response)")
    created_at: datetime

    @field_validator('saat', mode='before')
    @classmethod
    def heal_saat(cls, v: Any) -> Optional[str]:
        """Geçersiz saat formatını null'a çeker"""
        if not v: return None
        import re
        if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", str(v)):
            return None
        return str(v)

    @field_validator('mesafe_km', mode='before')
    @classmethod
    def heal_mesafe(cls, v: Any) -> int:
        """Geçersiz mesafeyi 1'e çeker (0 ve altı validasyon hatasıdır)"""
        try:
            val = int(float(v))
            return max(1, val)
        except (ValueError, TypeError):
            return 1

    model_config = ConfigDict(from_attributes=True)
