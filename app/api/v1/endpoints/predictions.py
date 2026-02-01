from typing import Annotated, Optional
from app.api.deps import SessionDep, get_current_user, get_current_active_admin
from app.database.models import Sofor, Kullanici
from app.schemas.prediction import PredictionRequest, PredictionResponse, TrainingResponse
from app.services.prediction_service import PredictionService
from fastapi import APIRouter, HTTPException, Depends, Query

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
async def predict_fuel(
    request: PredictionRequest, 
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Sefer senaryosu için yakıt tüketim tahmini yap.
    sofor_id verilirse veritabanından puan çekilir,
    sofor_score verilirse direkt kullanılır.
    """
    # Şoför puanını belirle
    sofor_score = 1.0  # Varsayılan

    if request.sofor_score is not None:
        # Doğrulanmış aralık: 0.1 (Kötü) - 2.0 (Mükemmel)
        if not (0.1 <= request.sofor_score <= 2.0):
             raise HTTPException(status_code=400, detail="Şoför puanı 0.1 ile 2.0 arasında olmalıdır")
        sofor_score = request.sofor_score
    elif request.sofor_id is not None:
        # Şoför puanını veritabanından çek
        sofor = await db.get(Sofor, request.sofor_id)
        if sofor:
            sofor_score = sofor.score or 1.0
        else:
            raise HTTPException(status_code=404, detail="Şoför bulunamadı")

    service = PredictionService()
    result = await service.predict_consumption(
        arac_id=request.arac_id,
        mesafe_km=request.mesafe_km,
        ton=request.ton,
        ascent_m=request.ascent_m,
        descent_m=request.descent_m,
        sofor_id=request.sofor_id
    )

    # result bir dict olabilir, tahmini_tuketim değerini al
    if isinstance(result, dict):
        tahmini = result.get("prediction_l_100km", result.get("tahmini_tuketim", 0))
        faktorler = result.get("faktorler", result.get("factors", None))
    else:
        tahmini = result
        faktorler = None

    # Güven aralığı hesapla (±10% basit yaklaşım, model uncertainty'den gelebilir)
    confidence_margin = tahmini * 0.10
    confidence_low = max(0, tahmini - confidence_margin)
    confidence_high = tahmini + confidence_margin

    return PredictionResponse(
        tahmini_tuketim=tahmini,
        model_used=request.model_type,
        confidence_low=round(confidence_low, 2),
        confidence_high=round(confidence_high, 2),
        faktorler=faktorler
    )

@router.post("/train/{arac_id}", response_model=TrainingResponse)
async def train_model(
    arac_id: int, 
    model_type: str, 
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)]
):
    """
    Train a model for a specific vehicle and return metrics.
    """
    service = PredictionService(db)

    if model_type == "linear":
        result = await service.train_linear_model(arac_id)
    elif model_type in ["ensemble", "xgboost"]:
        result = await service.train_xgboost_model(arac_id)
    else:
        raise HTTPException(status_code=400, detail="Geçersiz model tipi. linear veya ensemble seçin.")

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Eğitim hatası"))

    return TrainingResponse(
        status=result.get("status", "success"),
        model_type=result.get("model_type", model_type),
        r2_score=result.get("r2_score", 0.0) or result.get("model_r2", 0.0),
        sample_count=result.get("sample_count", 0),
        metrics=result
    )


# ============== TIME SERIES ENDPOINTS ==============

@router.get("/time-series/forecast")
async def get_weekly_forecast(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    arac_id: Optional[int] = None
):
    """
    LSTM modeli ile haftalık yakıt tahmini.
    
    Returns:
        {
            "forecast": [34.2, 33.8, 35.1, ...],
            "forecast_dates": ["2026-01-12", ...],
            "confidence_low": [32.1, ...],
            "confidence_high": [36.3, ...],
            "trend": "stable",
            "vehicle_id": int or null
        }
    """
    from app.services.time_series_service import get_time_series_service
    
    service = get_time_series_service()
    result = await service.predict_weekly(arac_id)
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Tahmin başarısız'))
    
    return result


@router.post("/time-series/train")
async def train_time_series_model(
    db: SessionDep,
    current_admin: Annotated[Kullanici, Depends(get_current_active_admin)],
    arac_id: Optional[int] = None,
    days: int = Query(180, ge=30, le=730),
    epochs: int = Query(100, ge=10, le=500)
):
    """
    LSTM zaman serisi modelini eğit.
    
    Args:
        arac_id: Araç ID (None = filo geneli)
        days: Eğitim için kullanılacak gün sayısı (30-730)
        epochs: Eğitim epoch sayısı (10-500)
    """
    from app.services.time_series_service import get_time_series_service
    
    service = get_time_series_service()
    result = await service.train_model(arac_id, days, epochs)
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Eğitim başarısız'))
    
    return result


@router.get("/time-series/trend")
async def get_trend_analysis(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    arac_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365)
):
    """
    Tüketim trend analizi.
    
    Returns:
        {
            "trend": "increasing" | "stable" | "decreasing",
            "trend_tr": "Artıyor" | "Sabit" | "Azalıyor",
            "slope": float,
            "current_avg": float,
            "previous_avg": float,
            "moving_average_7": [...]
        }
    """
    from app.services.time_series_service import get_time_series_service
    
    service = get_time_series_service()
    result = await service.get_trend_analysis(arac_id, days)
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Analiz başarısız'))
    
    return result


@router.get("/time-series/status")
async def get_time_series_status(
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """Zaman serisi model durumu."""
    from app.services.time_series_service import get_time_series_service
    
    service = get_time_series_service()
    return service.get_model_status()


# ============== ENSEMBLE MODEL STATUS ==============

@router.get("/ensemble/status")
async def get_ensemble_status(
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Ensemble model durumu ve kullanılabilir modeller.
    
    Returns:
        {
            "models": {
                "physics": true,
                "lightgbm": true/false,
                "xgboost": true/false,
                "gradient_boosting": true,
                "random_forest": true
            },
            "weights": {...},
            "sklearn_available": true/false,
            "lightgbm_available": true/false,
            "xgboost_available": true/false
        }
    """
    from app.core.ml.ensemble_predictor import (
        SKLEARN_AVAILABLE,
        XGBOOST_AVAILABLE,
        LIGHTGBM_AVAILABLE,
        EnsembleFuelPredictor
    )
    
    predictor = EnsembleFuelPredictor()
    
    return {
        "models": {
            "physics": True,
            "lightgbm": LIGHTGBM_AVAILABLE,
            "xgboost": XGBOOST_AVAILABLE,
            "gradient_boosting": SKLEARN_AVAILABLE,
            "random_forest": SKLEARN_AVAILABLE
        },
        "weights": predictor.WEIGHTS,
        "sklearn_available": SKLEARN_AVAILABLE,
        "lightgbm_available": LIGHTGBM_AVAILABLE,
        "xgboost_available": XGBOOST_AVAILABLE,
        "total_models": sum([
            1,  # Physics
            1 if LIGHTGBM_AVAILABLE else 0,
            1 if XGBOOST_AVAILABLE else 0,
            1 if SKLEARN_AVAILABLE else 0,  # GB
            1 if SKLEARN_AVAILABLE else 0   # RF
        ])
    }

