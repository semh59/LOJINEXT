"""
Şoför (Driver) Pydantic şemaları.

Güvenlik kontrolleri:
- İsim validasyonu (Türkçe karakter desteği)
- Telefon maskeleme (PII koruması)
- XSS koruması
"""

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.schemas.validators import (
    mask_phone,
    sanitize_string,
    validate_phone,
    validate_safe_string,
)


class SoforBase(BaseModel):
    """Şoför base model - ortak alanlar."""

    ad_soyad: str = Field(..., min_length=3, max_length=100)
    telefon: Optional[str] = Field(None, max_length=20, description="Telefon numarası")

    @field_validator("telefon")
    @classmethod
    def validate_phone_field(cls, v: Optional[str]) -> Optional[str]:
        """Telefon formatı kontrolü."""
        return validate_phone(v)

    ise_baslama: Optional[date] = None
    ehliyet_sinifi: Literal["B", "C", "D", "E", "G", "CE", "D1E"] = Field("E")
    score: float = Field(1.0, ge=0.1, le=2.0, description="Sonuç puanı (0.1-2.0)")
    manual_score: float = Field(
        1.0, ge=0.1, le=2.0, description="Manuel değerlendirme puanı"
    )
    aktif: bool = True
    notlar: Optional[str] = Field(None, max_length=500)

    @field_validator("ad_soyad", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """İsim sanitize ve title case."""
        if isinstance(v, str):
            v = sanitize_string(v)
            # Title case (Türkçe uyumlu)
            v = v.title()
        return v

    @field_validator("telefon", mode="before")
    @classmethod
    def sanitize_phone(cls, v: Optional[str]) -> Optional[str]:
        """Telefon sanitize."""
        if isinstance(v, str):
            v = sanitize_string(v)
        return v

    @field_validator("notlar", mode="before")
    @classmethod
    def validate_notlar(cls, v: Optional[str]) -> Optional[str]:
        """Notlar alanı XSS koruması."""
        return validate_safe_string(v)


class SoforCreate(SoforBase):
    """Şoför oluşturma şeması."""

    pass


class SoforUpdate(BaseModel):
    """Şoför güncelleme şeması - tüm alanlar optional."""

    ad_soyad: Optional[str] = Field(None, min_length=3, max_length=100)
    telefon: Optional[str] = Field(None, max_length=20)
    ise_baslama: Optional[date] = None
    ehliyet_sinifi: Optional[Literal["B", "C", "D", "E", "G", "CE", "D1E"]] = None
    score: Optional[float] = Field(None, ge=0.1, le=2.0)
    manual_score: Optional[float] = Field(None, ge=0.1, le=2.0)
    hiz_disiplin_skoru: Optional[float] = Field(
        None, ge=0.1, le=2.0, description="Hız Disiplin Skoru"
    )
    agresif_surus_faktoru: Optional[float] = Field(
        None, ge=0.1, le=2.0, description="Agresif Sürüş Faktörü"
    )
    aktif: Optional[bool] = None
    notlar: Optional[str] = Field(None, max_length=500)

    @field_validator("ad_soyad", mode="before")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """İsim sanitize ve title case."""
        if isinstance(v, str):
            v = sanitize_string(v)
            v = v.title()
        return v

    @field_validator("telefon")
    @classmethod
    def validate_phone_field(cls, v: Optional[str]) -> Optional[str]:
        """Telefon formatı kontrolü."""
        return validate_phone(v)

    @field_validator("notlar", mode="before")
    @classmethod
    def validate_notlar(cls, v: Optional[str]) -> Optional[str]:
        """Notlar alanı XSS koruması."""
        return validate_safe_string(v)

    @field_validator("score", "manual_score")
    @classmethod
    def validate_scores(cls, v: Optional[float]) -> Optional[float]:
        """Puan aralık kontrolü."""
        if v is not None and (v < 0.1 or v > 2.0):
            raise ValueError("Puan 0.1-2.0 arasında olmalı")
        return v


class SoforResponse(SoforBase):
    """Şoför response şeması - API çıktısı."""

    id: int
    ad_soyad: str = Field(..., description="Permissive name")
    ise_baslama: Optional[date] = None
    created_at: datetime

    # Override to be permissive on read
    ehliyet_sinifi: str = Field("E")

    @field_validator("ehliyet_sinifi", mode="before")
    @classmethod
    def validate_license_class(cls, v: Optional[str]) -> str:
        """Ehliyet sınıfı bozuksa (örn: lowercase) düzelt veya varsayılan ata."""
        valid_classes = {"B", "C", "D", "E", "G", "CE", "D1E"}
        if isinstance(v, str):
            v_upper = v.upper().strip()
            if v_upper in valid_classes:
                return v_upper
        # Fallback for invalid/empty data in DB
        return "E"

    # Telefon maskelenmiş olarak dönülür (PII koruması)
    @computed_field
    @property
    def telefon_masked(self) -> Optional[str]:
        """Maskelenmiş telefon numarası."""
        return mask_phone(self.telefon)

    @field_validator("ad_soyad", mode="before")
    @classmethod
    def heal_name(cls, v: Any) -> str:
        """Kısa veya bozuk isimleri düzeltir."""
        if not v:
            return "İSİMSİZ SÜRÜCÜ"
        name = str(v).strip()
        if len(name) < 3:
            return f"{name} (Kısa İsim)"
        return name

    @field_validator("manual_score", "score", mode="before")
    @classmethod
    def heal_scores(cls, v: Any) -> float:
        """NULL veya bozuk puanları 1.0 olarak düzeltir."""
        if v is None:
            return 1.0
        try:
            val = float(v)
            if 0.1 <= val <= 2.0:
                return val
            return 1.0
        except (ValueError, TypeError, Exception):
            return 1.0

    @field_validator("ise_baslama", mode="before")
    @classmethod
    def heal_date(cls, v: Any) -> Optional[date]:
        """Bozuk tarihleri null yapar."""
        if not v:
            return None
        if isinstance(v, date):
            return v
        try:
            return date.fromisoformat(str(v).split("T")[0])
        except (ValueError, TypeError, Exception):
            return None

    model_config = ConfigDict(from_attributes=True)


class DriverPerformanceSchema(BaseModel):
    """Sürücü Performans Karnesi (AI Analizli)"""

    safety_score: float = Field(..., ge=0, le=100, description="Güvenli Sürüş Puanı")
    eco_score: float = Field(..., ge=0, le=100, description="Ekonomik Sürüş Puanı")
    compliance_score: float = Field(
        ..., ge=0, le=100, description="Kurallara Uyum Puanı"
    )
    total_score: float = Field(
        ..., ge=0, le=100, description="Genel Performans Puanı (Ağırlıklı)"
    )
    trend: Literal["increasing", "decreasing", "stable"] = "stable"
    total_km: float = 0
    total_trips: int = 0
