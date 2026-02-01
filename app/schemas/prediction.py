"""
Tahmin (Prediction) Pydantic şemaları.

ML model tahminleri için request/response şemaları.
Güvenlik: Dict boyut limiti, tip güvenliği.
"""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import validate_dict_size


# Maksimum metrics dict boyutu
MAX_METRICS_KEYS = 50


class PredictionRequest(BaseModel):
    """ML tahmin isteği şeması."""
    
    arac_id: int = Field(..., gt=0, le=999999999, description="Araç ID")
    mesafe_km: float = Field(..., gt=0, le=100000, description="Mesafe (km)")
    ton: float = Field(0.0, ge=0, le=1000, description="Yük ağırlığı (ton)")
    ascent_m: float = Field(0.0, ge=0, le=50000, description="Toplam tırmanış (m)")
    descent_m: float = Field(0.0, ge=0, le=50000, description="Toplam iniş (m)")
    sofor_id: Optional[int] = Field(
        None, 
        gt=0,
        description="Şoför ID (otomatik puan çekmek için)"
    )
    sofor_score: Optional[float] = Field(
        None, 
        ge=0.1, 
        le=2.0, 
        description="Manuel şoför puanı (0.1-2.0)"
    )
    model_type: Literal["linear", "xgboost"] = Field(
        "linear",
        description="Kullanılacak ML model tipi"
    )


class PredictionResponse(BaseModel):
    """ML tahmin yanıtı şeması."""
    
    tahmini_tuketim: float = Field(..., ge=0, description="Tahmini tüketim (litre)")
    model_used: Literal["linear", "xgboost"]
    status: Literal["success", "failure"] = "success"
    confidence_low: Optional[float] = Field(None, ge=0, description="Güven aralığı alt sınır")
    confidence_high: Optional[float] = Field(None, ge=0, description="Güven aralığı üst sınır")
    faktorler: Optional[Dict[str, float]] = Field(None, description="Tahmin faktör breakdown")


class TrainingResponse(BaseModel):
    """Model eğitim yanıtı şeması."""
    
    status: str = Field(..., max_length=50)
    model_type: str = Field(..., max_length=20)
    r2_score: float = Field(..., ge=-1.0, le=1.0, description="R² skoru")
    sample_count: int = Field(..., ge=0, description="Eğitim örneği sayısı")
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Ek metrikler (max 50 anahtar)"
    )
    
    @field_validator('metrics', mode='before')
    @classmethod
    def validate_metrics_size(cls, v: Optional[Dict]) -> Optional[Dict]:
        """Metrics dict boyut kontrolü - DoS koruması."""
        return validate_dict_size(v, max_keys=MAX_METRICS_KEYS)
    
    @field_validator('metrics')
    @classmethod
    def validate_metrics_values(cls, v: Optional[Dict]) -> Optional[Dict]:
        """Metrics değerlerinin serializable olduğunu kontrol et."""
        if v is None:
            return v
        
        # İzin verilen tipler
        allowed_types = (int, float, str, bool, type(None), list, dict)
        
        def check_value(val: Any, depth: int = 0) -> bool:
            if depth > 5:  # Maksimum derinlik
                raise ValueError("Metrics çok derin iç içe yapı içeriyor")
            
            if not isinstance(val, allowed_types):
                raise ValueError(f"Metrics desteklenmeyen tip içeriyor: {type(val)}")
            
            if isinstance(val, dict):
                for k, sub_v in val.items():
                    if not isinstance(k, str):
                        raise ValueError("Metrics anahtarları string olmalı")
                    check_value(sub_v, depth + 1)
            elif isinstance(val, list):
                for item in val:
                    check_value(item, depth + 1)
            
            return True
        
        for key, value in v.items():
            check_value(value)
        
        return v
