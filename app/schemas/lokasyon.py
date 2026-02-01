from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class LokasyonBase(BaseModel):
    cikis_yeri: str = Field(..., max_length=100)
    varis_yeri: str = Field(..., max_length=100)
    mesafe_km: int = Field(..., gt=0)
    tahmini_sure_saat: Optional[float] = Field(None, ge=0)
    zorluk: str = Field('Normal', max_length=20)  # Düz, Hafif Eğimli, Dik/Dağlık
    cikis_lat: Optional[float] = Field(None)
    cikis_lon: Optional[float] = Field(None)
    varis_lat: Optional[float] = Field(None)
    varis_lon: Optional[float] = Field(None)
    ascent_m: Optional[float] = Field(None, ge=0, description="Toplam yokuş yukarı (metre)")
    descent_m: Optional[float] = Field(None, ge=0, description="Toplam yokuş aşağı (metre)")
    notlar: Optional[str] = None

class LokasyonCreate(LokasyonBase):
    pass

class LokasyonUpdate(BaseModel):
    cikis_yeri: Optional[str] = Field(None, max_length=100)
    varis_yeri: Optional[str] = Field(None, max_length=100)
    mesafe_km: Optional[int] = Field(None, gt=0)
    tahmini_sure_saat: Optional[float] = Field(None, ge=0)
    zorluk: Optional[str] = Field(None, max_length=20)
    cikis_lat: Optional[float] = None
    cikis_lon: Optional[float] = None
    varis_lat: Optional[float] = None
    varis_lon: Optional[float] = None
    ascent_m: Optional[float] = Field(None, ge=0)
    descent_m: Optional[float] = Field(None, ge=0)
    notlar: Optional[str] = None

class LokasyonResponse(LokasyonBase):
    id: int
    api_mesafe_km: Optional[float] = None
    api_sure_saat: Optional[float] = None
    tahmini_yakit_lt: Optional[float] = None
    last_api_call: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
