from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LokasyonBase(BaseModel):
    cikis_yeri: str = Field(..., max_length=100)
    varis_yeri: str = Field(..., max_length=100)
    mesafe_km: float = Field(..., gt=0)
    tahmini_sure_saat: Optional[float] = Field(None, ge=0)
    zorluk: str = Field("Normal", max_length=20)  # Düz, Hafif Eğimli, Dik/Dağlık
    cikis_lat: Optional[float] = Field(None, ge=-90, le=90)
    cikis_lon: Optional[float] = Field(None, ge=-180, le=180)
    varis_lat: Optional[float] = Field(None, ge=-90, le=90)
    varis_lon: Optional[float] = Field(None, ge=-180, le=180)
    ascent_m: Optional[float] = Field(
        None, ge=0, description="Toplam yokuş yukarı (metre)"
    )
    descent_m: Optional[float] = Field(
        None, ge=0, description="Toplam yokuş aşağı (metre)"
    )
    flat_distance_km: float = Field(0.0, ge=0, description="Düz yol mesafesi (km)")
    otoban_mesafe_km: Optional[float] = Field(
        None, ge=0, description="Otoban mesafesi (km)"
    )
    sehir_ici_mesafe_km: Optional[float] = Field(
        None, ge=0, description="Şehiriçi/Kırsal mesafe (km)"
    )
    notlar: Optional[str] = None
    aktif: bool = True


class LokasyonCreate(LokasyonBase):
    pass


class LokasyonUpdate(BaseModel):
    cikis_yeri: Optional[str] = Field(None, max_length=100)
    varis_yeri: Optional[str] = Field(None, max_length=100)
    mesafe_km: Optional[float] = Field(None, gt=0)
    tahmini_sure_saat: Optional[float] = Field(None, ge=0)
    zorluk: Optional[str] = Field(None, max_length=20)
    cikis_lat: Optional[float] = Field(None, ge=-90, le=90)
    cikis_lon: Optional[float] = Field(None, ge=-180, le=180)
    varis_lat: Optional[float] = Field(None, ge=-90, le=90)
    varis_lon: Optional[float] = Field(None, ge=-180, le=180)
    ascent_m: Optional[float] = Field(None, ge=0)
    descent_m: Optional[float] = Field(None, ge=0)
    flat_distance_km: Optional[float] = Field(None, ge=0)
    otoban_mesafe_km: Optional[float] = Field(None, ge=0)
    sehir_ici_mesafe_km: Optional[float] = Field(None, ge=0)
    notlar: Optional[str] = None


class LokasyonResponse(LokasyonBase):
    id: int
    api_mesafe_km: Optional[float] = None
    api_sure_saat: Optional[float] = None
    tahmini_yakit_lt: Optional[float] = None
    last_api_call: Optional[datetime] = None
    route_analysis: Optional[dict] = None
    source: Optional[str] = Field(
        None, description="Veri kaynağı (api, mapbox_hybrid, etc.)"
    )
    is_corrected: bool = Field(False, description="Veri düzeltildi mi?")
    correction_reason: Optional[str] = Field(None, description="Düzeltme nedeni")

    model_config = ConfigDict(from_attributes=True)


class LokasyonPaginationResponse(BaseModel):
    items: List[LokasyonResponse]
    total: int
