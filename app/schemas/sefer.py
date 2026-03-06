"""
Sefer (Trip) Pydantic şemaları.

Güvenlik kontrolleri:
- XSS koruması (çıkış/varış yerleri)
- String sanitizasyonu
- Numeric constraints
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.validators import validate_safe_string


class SeferBase(BaseModel):
    """Sefer base model - ortak alanlar."""

    sefer_no: Optional[str] = Field(None, max_length=50, description="Sefer Numarası")
    tarih: date
    saat: Optional[str] = Field(
        None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="HH:mm formatı"
    )
    arac_id: int = Field(..., gt=0)
    dorse_id: Optional[int] = Field(None, gt=0, description="Dorse ID")
    sofor_id: int = Field(..., gt=0)
    guzergah_id: Optional[int] = Field(None, gt=0, description="Güzergah ID")

    # Weight Info
    bos_agirlik_kg: int = Field(0, ge=0)
    dolu_agirlik_kg: int = Field(0, ge=0)
    net_kg: int = Field(0, ge=0)
    ton: float = Field(0.0, ge=0.0)

    # Location
    cikis_yeri: str = Field(..., min_length=1, max_length=100)
    varis_yeri: str = Field(..., min_length=1, max_length=100)
    mesafe_km: float = Field(..., gt=0, le=10000)
    baslangic_km: Optional[int] = Field(None, ge=0, le=9999999)
    bitis_km: Optional[int] = Field(None, ge=0, le=9999999)

    bos_sefer: bool = False
    durum: Literal[
        "Tamam", "Devam Ediyor", "İptal", "Planlandı", "Yolda", "Bekliyor"
    ] = Field("Tamam")
    dagitilan_yakit: Optional[Decimal] = Field(None, ge=0, le=10000)
    tuketim: Optional[float] = Field(None, ge=0, le=1000)
    ascent_m: Optional[float] = Field(None, ge=0, le=50000)
    descent_m: Optional[float] = Field(None, ge=0, le=50000)
    flat_distance_km: float = Field(0.0, ge=0.0, le=10000)
    otoban_mesafe_km: Optional[float] = Field(None, ge=0)
    sehir_ici_mesafe_km: Optional[float] = Field(None, ge=0)
    rota_detay: Optional[dict] = None
    notlar: Optional[str] = Field(None, max_length=255)
    is_real: bool = Field(False, description="Data Guarding: Synthetic vs Real")

    @field_validator("cikis_yeri", "varis_yeri", mode="before")
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        """Lokasyon alanları XSS koruması."""
        return validate_safe_string(v)

    @field_validator("tarih", mode="after")
    @classmethod
    def validate_tarih_not_future(cls, v: date) -> date:
        """Tarih alanı gelecekteki bir tarih olamaz."""
        if v > date.today():
            raise ValueError("Kayıt tarihi gelecekteki bir gün olamaz")
        return v


class SeferCreate(SeferBase):
    """Sefer oluşturma şeması."""

    guzergah_id: Optional[int] = Field(None, gt=0, description="Güzergah ID")

    # Round-trip support
    is_round_trip: bool = Field(False, description="Gidiş-dönüş seferi mi?")
    return_net_kg: Optional[int] = Field(0, ge=0, description="Dönüş yükü (kg)")
    return_sefer_no: Optional[str] = Field(
        None, max_length=50, description="Dönüş sefer no"
    )

    @model_validator(mode="after")
    def validate_km_range(self) -> "SeferCreate":
        """Bitiş km başlangıç'tan büyük olmalı."""
        if self.baslangic_km is not None and self.bitis_km is not None:
            if self.bitis_km < self.baslangic_km:
                raise ValueError("Bitiş km, başlangıç km'den büyük olmalı")
        return self


class SeferUpdate(BaseModel):
    """
    Sefer güncelleme şeması - tüm alanlar optional.
    """

    tarih: Optional[date] = None
    saat: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    arac_id: Optional[int] = Field(None, gt=0)
    dorse_id: Optional[int] = Field(None, gt=0)
    sofor_id: Optional[int] = Field(None, gt=0)
    guzergah_id: Optional[int] = Field(None, gt=0)

    bos_agirlik_kg: Optional[int] = Field(None, ge=0)
    dolu_agirlik_kg: Optional[int] = Field(None, ge=0)
    net_kg: Optional[int] = Field(None, ge=0)
    ton: Optional[float] = Field(None, ge=0.0)

    cikis_yeri: Optional[str] = Field(None, min_length=1, max_length=100)
    varis_yeri: Optional[str] = Field(None, min_length=1, max_length=100)
    mesafe_km: Optional[float] = Field(None, gt=0)
    baslangic_km: Optional[int] = Field(None, ge=0)
    bitis_km: Optional[int] = Field(None, ge=0)

    bos_sefer: Optional[bool] = None
    durum: Optional[
        Literal["Tamam", "Devam Ediyor", "İptal", "Planlandı", "Yolda", "Bekliyor"]
    ] = None
    periyot_id: Optional[int] = Field(None, gt=0)
    dagitilan_yakit: Optional[Decimal] = Field(None, ge=0)
    tuketim: Optional[float] = Field(None, ge=0)
    ascent_m: Optional[float] = Field(None, ge=0)
    descent_m: Optional[float] = Field(None, ge=0)
    flat_distance_km: Optional[float] = Field(None, ge=0)
    notlar: Optional[str] = Field(None, max_length=255)
    is_real: Optional[bool] = None

    # Management fields added to support update
    sefer_no: Optional[str] = Field(None, max_length=50)
    is_round_trip: Optional[bool] = Field(None)
    return_net_kg: Optional[int] = Field(None, ge=0)
    return_sefer_no: Optional[str] = Field(None, max_length=50)
    is_real: Optional[bool] = Field(None)

    @field_validator("cikis_yeri", "varis_yeri", mode="before")
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        """Lokasyon alanları XSS koruması."""
        return validate_safe_string(v)

    @model_validator(mode="after")
    def validate_km_range(self) -> "SeferUpdate":
        """Bitiş km başlangıç'tan büyük olmalı."""
        if self.baslangic_km is not None and self.bitis_km is not None:
            if self.bitis_km < self.baslangic_km:
                raise ValueError("Bitiş km, başlangıç km'den büyük olmalı")
        return self

    model_config = ConfigDict(from_attributes=True)


class SeferResponse(SeferBase):
    """
    Sefer response şeması - API çıktısı.
    """

    id: int
    plaka: Optional[str] = None
    dorse_plakasi: Optional[str] = None
    sofor_adi: Optional[str] = None
    guzergah_adi: Optional[str] = None
    periyot_id: Optional[int] = None
    saat: Optional[str] = Field(None, description="HH:mm formatı")

    tahmini_tuketim: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SeferMeta(BaseModel):
    """Sefer listesi için metadata."""

    total: int
    skip: int
    limit: int


class SeferListResponse(BaseModel):
    """Standardize sefer listesi yanıtı."""

    items: List[SeferResponse]
    meta: SeferMeta


# Model Rebuild (Elite Stability)
SeferResponse.model_rebuild()
SeferListResponse.model_rebuild()


class SeferStatsResponse(BaseModel):
    """Materialized View bazlı performans dostu Sefer istatistikleri."""

    toplam_sefer: int = 0
    toplam_km: float = 0.0
    highway_km: float = 0.0
    total_ascent: float = 0.0
    total_weight: float = 0.0
    avg_highway_pct: int = 0
    last_updated: Optional[datetime] = None


class SeferBulkStatusUpdate(BaseModel):
    """Toplu durum güncelleme isteği."""

    sefer_ids: List[int] = Field(..., min_length=1)
    new_status: Literal[
        "Tamam", "Devam Ediyor", "İptal", "Planlandı", "Yolda", "Bekliyor"
    ]


class SeferBulkCancel(BaseModel):
    """Toplu iptal isteği."""

    sefer_ids: List[int] = Field(..., min_length=1)
    iptal_nedeni: str = Field(..., min_length=5, max_length=255)


class BulkErrorDetail(BaseModel):
    """Bul işlem hata detayı."""

    id: int
    reason: str


class SeferBulkResponse(BaseModel):
    """Toplu işlem yanıtı."""

    success_count: int
    failed_count: int
    failed: List[BulkErrorDetail] = []
