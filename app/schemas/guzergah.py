from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class GuzergahBase(BaseModel):
    ad: Optional[str] = Field(None, min_length=2, max_length=100)
    cikis_yeri: str = Field(..., min_length=2, max_length=100)
    varis_yeri: str = Field(..., min_length=2, max_length=100)
    mesafe_km: int = Field(..., gt=0)
    varsayilan_arac_id: Optional[int] = Field(None, gt=0)
    varsayilan_sofor_id: Optional[int] = Field(None, gt=0)
    notlar: Optional[str] = None
    aktif: bool = True

class GuzergahCreate(GuzergahBase):
    pass

class GuzergahUpdate(BaseModel):
    ad: Optional[str] = Field(None, min_length=2, max_length=100)
    cikis_yeri: Optional[str] = Field(None, min_length=2, max_length=100)
    varis_yeri: Optional[str] = Field(None, min_length=2, max_length=100)
    mesafe_km: Optional[int] = Field(None, gt=0)
    varsayilan_arac_id: Optional[int] = Field(None, gt=0)
    varsayilan_sofor_id: Optional[int] = Field(None, gt=0)
    notlar: Optional[str] = None
    aktif: Optional[bool] = None

class GuzergahResponse(GuzergahBase):
    id: int
    created_at: datetime
    varsayilan_arac_plaka: Optional[str] = None
    varsayilan_sofor_ad: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
