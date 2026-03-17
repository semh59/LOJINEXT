"""
Sefer (Trip) Pydantic semalari.

Guvenlik kontrolleri:
- XSS korumasi (cikis/varis yerleri)
- String sanitizasyonu
- Numeric constraints
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.utils.sefer_status import ensure_canonical_sefer_status
from app.schemas.validators import validate_safe_string

SeferDurum = Literal[
    "Tamam",
    "Tamamlandı",
    "Devam Ediyor",
    "İptal",
    "Planlandı",
    "Yolda",
    "Bekliyor",
]


class SeferBase(BaseModel):
    """Sefer base model."""

    sefer_no: Optional[str] = Field(None, max_length=50)
    tarih: date
    saat: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    arac_id: int = Field(..., gt=0)
    dorse_id: Optional[int] = Field(None, gt=0)
    sofor_id: int = Field(..., gt=0)
    guzergah_id: Optional[int] = Field(None, gt=0)

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
    durum: SeferDurum = Field("Tamam")
    dagitilan_yakit: Optional[Decimal] = Field(None, ge=0, le=10000)
    tuketim: Optional[float] = Field(None, ge=0, le=1000)
    ascent_m: Optional[float] = Field(None, ge=0, le=50000)
    descent_m: Optional[float] = Field(None, ge=0, le=50000)
    flat_distance_km: float = Field(0.0, ge=0.0, le=10000)
    otoban_mesafe_km: Optional[float] = Field(None, ge=0)
    sehir_ici_mesafe_km: Optional[float] = Field(None, ge=0)
    rota_detay: Optional[dict] = None
    tahmin_meta: Optional[dict] = None
    notlar: Optional[str] = Field(None, max_length=255)
    is_real: bool = Field(False)

    @field_validator("cikis_yeri", "varis_yeri", mode="before")
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_string(v)

    @field_validator("durum", mode="before")
    @classmethod
    def normalize_durum(cls, v: Optional[str]) -> Optional[str]:
        return ensure_canonical_sefer_status(v, field_name="durum", allow_none=False)

    @field_validator("mesafe_km", mode="before")
    @classmethod
    def heal_mesafe(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            return 1.0
        return v

    @field_validator("tarih", mode="after")
    @classmethod
    def validate_tarih_not_future(cls, v: date) -> date:
        if v > date.today() + timedelta(days=365):
            raise ValueError("Tarih en fazla 365 gun ileri olabilir")
        return v


class SeferCreate(SeferBase):
    """Sefer olusturma semasi."""

    guzergah_id: int = Field(..., gt=0)

    # Round-trip support
    is_round_trip: bool = Field(False)
    return_net_kg: Optional[int] = Field(0, ge=0)
    return_sefer_no: Optional[str] = Field(None, max_length=50)

    @model_validator(mode="after")
    def validate_km_range(self) -> "SeferCreate":
        if self.baslangic_km is not None and self.bitis_km is not None:
            if self.bitis_km < self.baslangic_km:
                raise ValueError("Bitis km buyuk olmali")
        return self


class SeferUpdate(BaseModel):
    """Sefer guncelleme semasi."""

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
    durum: Optional[SeferDurum] = None
    periyot_id: Optional[int] = Field(None, gt=0)
    dagitilan_yakit: Optional[Decimal] = Field(None, ge=0)
    tuketim: Optional[float] = Field(None, ge=0)
    ascent_m: Optional[float] = Field(None, ge=0)
    descent_m: Optional[float] = Field(None, ge=0)
    flat_distance_km: Optional[float] = Field(None, ge=0)
    tahmin_meta: Optional[dict] = None
    notlar: Optional[str] = Field(None, max_length=255)
    is_real: Optional[bool] = None
    iptal_nedeni: Optional[str] = Field(None, max_length=255)

    sefer_no: Optional[str] = Field(None, max_length=50)
    is_round_trip: Optional[bool] = Field(None)
    return_net_kg: Optional[int] = Field(None, ge=0)
    return_sefer_no: Optional[str] = Field(None, max_length=50)
    # B-004: Optimistic Locking
    version: Optional[int] = Field(None, ge=1)

    @field_validator("cikis_yeri", "varis_yeri", mode="before")
    @classmethod
    def validate_location(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_string(v)

    @field_validator("durum", mode="before")
    @classmethod
    def normalize_durum(cls, v: Optional[str]) -> Optional[str]:
        return ensure_canonical_sefer_status(v, field_name="durum", allow_none=True)

    @field_validator("mesafe_km", mode="before")
    @classmethod
    def heal_mesafe(cls, v: Any) -> Any:
        if isinstance(v, (int, float)) and v <= 0:
            return 1.0
        return v

    @model_validator(mode="after")
    def validate_km_range(self) -> "SeferUpdate":
        if self.baslangic_km is not None and self.bitis_km is not None:
            if self.bitis_km < self.baslangic_km:
                raise ValueError("Bitis km buyuk olmali")
        return self

    model_config = ConfigDict(from_attributes=True)


class SeferResponse(SeferBase):
    """Sefer response semasi."""

    id: int
    plaka: Optional[str] = None
    dorse_plakasi: Optional[str] = None
    sofor_adi: Optional[str] = None
    guzergah_adi: Optional[str] = None
    periyot_id: Optional[int] = None
    saat: Optional[str] = Field(None)

    @field_validator("saat", mode="before")
    @classmethod
    def heal_saat(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        import re

        if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", v):
            return None
        return v

    tahmini_tuketim: Optional[float] = None
    created_at: datetime
    version: int = 1  # B-004: Optimistic locking version

    model_config = ConfigDict(from_attributes=True)


class SeferMeta(BaseModel):
    """Sefer listesi icin metadata."""

    total: int
    skip: int
    limit: int


class SeferListResponse(BaseModel):
    """Standardize sefer listesi yaniti."""

    items: List[SeferResponse]
    meta: SeferMeta


# Model Rebuild
SeferResponse.model_rebuild()
SeferListResponse.model_rebuild()


class SeferStatsResponse(BaseModel):
    """Sefer istatistikleri."""

    toplam_sefer: int = 0
    toplam_km: float = 0.0
    highway_km: float = 0.0
    total_ascent: float = 0.0
    total_weight: float = 0.0
    avg_highway_pct: int = 0
    last_updated: Optional[datetime] = None


class SeferBulkStatusUpdate(BaseModel):
    """Toplu durum guncelleme."""

    sefer_ids: List[int] = Field(..., min_length=1)
    new_status: SeferDurum

    @field_validator("new_status", mode="before")
    @classmethod
    def normalize_new_status(cls, v: Optional[str]) -> Optional[str]:
        return ensure_canonical_sefer_status(
            v, field_name="new_status", allow_none=False
        )


class SeferBulkCancel(BaseModel):
    """Toplu iptal."""

    sefer_ids: List[int] = Field(..., min_length=1)
    iptal_nedeni: str = Field(..., min_length=5, max_length=255)


class SeferBulkDelete(BaseModel):
    """Toplu silme."""

    sefer_ids: List[int] = Field(..., min_length=1)


class BulkErrorDetail(BaseModel):
    """Hata detayi."""

    id: int
    reason: str


class SeferBulkResponse(BaseModel):
    """Toplu islem yaniti."""

    success_count: int
    failed_count: int
    failed: List[BulkErrorDetail] = []
