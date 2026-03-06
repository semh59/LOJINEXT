"""
Kullanıcı (User) Pydantic şemaları - LojiNext Elite Modernized.

Gelişmiş RBAC ve Email tabanlı kimlik doğrulama.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import validate_password_complexity


class RolRead(BaseModel):
    """Rol response şeması"""

    id: int
    ad: str
    yetkiler: dict
    olusturma: datetime

    model_config = ConfigDict(from_attributes=True)


class KullaniciBase(BaseModel):
    """Kullanıcı base model - ortak alanlar."""

    email: str = Field(..., description="Kurumsal e-posta adresi veya kullanıcı adı")
    ad_soyad: str = Field(..., min_length=2, max_length=100)
    aktif: bool = True
    sofor_id: Optional[int] = None


class KullaniciCreate(KullaniciBase):
    """Kullanıcı oluşturma şeması."""

    rol_id: int
    sifre: str = Field(..., min_length=8, max_length=128)

    @field_validator("sifre")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password complexity validation."""
        return validate_password_complexity(v)


class KullaniciUpdate(BaseModel):
    """Kullanıcı güncelleme şeması."""

    email: Optional[str] = None
    ad_soyad: Optional[str] = None
    rol_id: Optional[int] = None
    aktif: Optional[bool] = None
    sifre: Optional[str] = Field(None, min_length=8, max_length=128)

    @field_validator("sifre")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Password complexity validation for updates."""
        if v is None:
            return v
        return validate_password_complexity(v)


class KullaniciRead(KullaniciBase):
    """Kullanıcı response şeması."""

    id: Optional[int] = None
    rol_id: int
    rol: Optional[RolRead] = None
    created_at: datetime
    updated_at: datetime
    son_giris: Optional[datetime] = None
    son_giris_ip: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
