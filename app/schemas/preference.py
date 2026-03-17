from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PreferenceBase(BaseModel):
    modul: str
    ayar_tipi: str
    deger: Any
    ad: Optional[str] = None
    is_default: bool = False


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceItem(PreferenceBase):
    id: int
    kullanici_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PreferenceListResponse(BaseModel):
    items: List[PreferenceItem]
