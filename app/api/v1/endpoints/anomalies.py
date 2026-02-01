"""
LojiNext AI - Anomali API Endpoint'leri
"""

from typing import List, Optional, Annotated

from app.api.deps import get_current_user, SessionDep
from app.database.models import Kullanici
from app.core.services.anomaly_detector import (
    SeverityEnum,
    get_anomaly_detector,
)
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

router = APIRouter()


class AnomalyResponse(BaseModel):
    tip: str
    kaynak_tip: str
    kaynak_id: int
    deger: float
    beklenen_deger: float
    sapma_yuzde: float
    severity: str
    aciklama: str
    tarih: Optional[str] = None


class AnomalySummaryResponse(BaseModel):
    tuketim: dict
    maliyet: dict
    sefer: dict
    total_count: int


class DetectRequest(BaseModel):
    arac_id: Optional[int] = None
    consumptions: Optional[List[float]] = None
    use_ml: bool = True


@router.post("/detect/consumption", response_model=List[AnomalyResponse])
async def detect_consumption_anomalies(
    request: DetectRequest,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Tüketim anomalilerini tespit et
    
    Args:
        consumptions: Tüketim değerleri listesi
        arac_id: Araç ID'si (opsiyonel)
        use_ml: ML kullanılsın mı
    """
    if not request.consumptions or len(request.consumptions) < 5:
        raise HTTPException(
            status_code=400,
            detail="En az 5 tüketim değeri gerekli"
        )
    if len(request.consumptions) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Maksimum 1000 veri noktası analiz edilebilir"
        )

    detector = get_anomaly_detector()
    anomalies = await detector.detect_consumption_anomalies(
        request.consumptions,
        arac_id=request.arac_id,
        use_ml=request.use_ml
    )

    return [
        AnomalyResponse(
            tip=a.tip.value,
            kaynak_tip=a.kaynak_tip,
            kaynak_id=a.kaynak_id,
            deger=a.deger,
            beklenen_deger=a.beklenen_deger,
            sapma_yuzde=a.sapma_yuzde,
            severity=a.severity.value,
            aciklama=a.aciklama,
            tarih=a.tarih.isoformat() if a.tarih else None
        )
        for a in anomalies
    ]


@router.get("/recent", response_model=List[AnomalyResponse])
async def get_recent_anomalies(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=365),
    severity: Optional[str] = Query(None)
):
    """
    Son X günün anomalilerini getir
    
    Args:
        days: Kaç gün geriye bakılacak
        severity: Ciddiyet filtresi (low, medium, high, critical)
    """
    detector = get_anomaly_detector()

    severity_enum = None
    if severity:
        try:
            severity_enum = SeverityEnum(severity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Geçersiz severity: {severity}. Geçerli değerler: low, medium, high, critical"
            )

    anomalies = await detector.get_recent_anomalies(days=days, severity=severity_enum)

    return [
        AnomalyResponse(
            tip=a.get('tip', ''),
            kaynak_tip=a.get('kaynak_tip', ''),
            kaynak_id=a.get('kaynak_id', 0),
            deger=a.get('deger', 0),
            beklenen_deger=a.get('beklenen_deger', 0),
            sapma_yuzde=a.get('sapma_yuzde', 0),
            severity=a.get('severity', ''),
            aciklama=a.get('aciklama', ''),
            tarih=a.get('tarih')
        )
        for a in anomalies
    ]


@router.get("/summary")
async def get_anomaly_summary(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Son 30 günün anomali özeti
    """
    detector = get_anomaly_detector()
    try:
        from app.database.models import Anomaly
        from sqlalchemy import func, case, select
        from datetime import datetime, timedelta
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Optimized DB aggregation instead of fetching all
        stmt = select(
            Anomaly.tip,
            Anomaly.severity,
            func.count(Anomaly.id).label('count')
        ).where(
            Anomaly.tarih >= thirty_days_ago
        ).group_by(Anomaly.tip, Anomaly.severity)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        summary = {'tuketim': {}, 'maliyet': {}, 'sefer': {}}
        total = 0
        
        for row in rows:
            tip = row.tip
            severity = row.severity.value if hasattr(row.severity, 'value') else row.severity
            count = row.count
            
            # Map known types, fallback to tuketim if unknown for safety
            target_tip = 'tuketim'
            if 'maliyet' in str(tip).lower(): target_tip = 'maliyet'
            elif 'sefer' in str(tip).lower(): target_tip = 'sefer'
            elif str(tip).lower() in summary: target_tip = str(tip).lower()
            
            summary[target_tip][severity] = summary[target_tip].get(severity, 0) + count
            total += count

        return {
            "tuketim": summary.get('tuketim', {}),
            "maliyet": summary.get('maliyet', {}),
            "sefer": summary.get('sefer', {}),
            "total_count": total
        }
    except Exception as e:
        # Fallback empty if table issue
        return {"tuketim": {}, "maliyet": {}, "sefer": {}, "total_count": 0}
