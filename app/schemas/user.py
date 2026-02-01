"""
Kullanıcı (User) Pydantic şemaları.

Güvenlik kontrolleri:
- Kullanıcı adı strict alfanumerik
- Şifre complexity (min_length)
- Password response'da YOK
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.validators import sanitize_string, validate_username, validate_safe_string


class KullaniciBase(BaseModel):
    """Kullanıcı base model - ortak alanlar."""
    
    kullanici_adi: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Sadece harf, rakam ve alt çizgi"
    )
    ad_soyad: Optional[str] = Field(None, max_length=100)
    rol: Literal["admin", "user", "manager", "superadmin"] = Field(default="user")
    aktif: bool = True
    
    @field_validator('kullanici_adi', mode='before')
    @classmethod
    def validate_kullanici_adi(cls, v: str) -> str:
        """Kullanıcı adı validasyonu - strict alfanumerik."""
        if isinstance(v, str):
            v = sanitize_string(v)
        return v
    
    @field_validator('ad_soyad', mode='before')
    @classmethod
    def sanitize_ad_soyad(cls, v: Optional[str]) -> Optional[str]:
        """Ad soyad XSS koruması."""
        return validate_safe_string(v)


class KullaniciCreate(KullaniciBase):
    """Kullanıcı oluşturma şeması - şifre dahil."""
    
    sifre: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="Minimum 8 karakter"
    )
    
    @field_validator('sifre')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Şifre karmaşıklık kontrolü.
        - Minimum 8 karakter (Field'da tanımlı)
        - En az 1 büyük harf
        - En az 1 küçük harf
        - En az 1 rakam
        """
        if not any(c.isupper() for c in v):
            raise ValueError("Şifre en az 1 büyük harf içermeli")
        if not any(c.islower() for c in v):
            raise ValueError("Şifre en az 1 küçük harf içermeli")
        if not any(c.isdigit() for c in v):
            raise ValueError("Şifre en az 1 rakam içermeli")
        return v


class KullaniciUpdate(BaseModel):
    """Kullanıcı güncelleme şeması - tüm alanlar optional."""
    
    ad_soyad: Optional[str] = Field(None, max_length=100)
    sifre: Optional[str] = Field(None, min_length=8, max_length=128)
    rol: Optional[Literal["admin", "user", "manager", "superadmin"]] = None
    aktif: Optional[bool] = None
    
    @field_validator('sifre')
    @classmethod
    def validate_password_complexity(cls, v: Optional[str]) -> Optional[str]:
        """Şifre karmaşıklık kontrolü (güncelleme için)."""
        if v is None:
            return v
        if not any(c.isupper() for c in v):
            raise ValueError("Şifre en az 1 büyük harf içermeli")
        if not any(c.islower() for c in v):
            raise ValueError("Şifre en az 1 küçük harf içermeli")
        if not any(c.isdigit() for c in v):
            raise ValueError("Şifre en az 1 rakam içermeli")
        return v
    
    @field_validator('ad_soyad', mode='before')
    @classmethod
    def sanitize_ad_soyad(cls, v: Optional[str]) -> Optional[str]:
        """Ad soyad XSS koruması."""
        return validate_safe_string(v)


class KullaniciRead(KullaniciBase):
    """
    Kullanıcı response şeması - API çıktısı.
    
    ⚠️ SECURITY: sifre/password_hash bu modelde YOK!
    """
    
    id: int
    created_at: datetime
    son_giris: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
