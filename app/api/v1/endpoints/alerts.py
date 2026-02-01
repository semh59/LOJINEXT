"""
LojiNext AI - Uyarı (Alerts) API Endpoint'leri
Bildirim sistemi için backend API - Veritabanı destekli

Frontend'de zil simgesine tıklandığında bu API kullanılır.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Annotated

from app.api.deps import SessionDep, get_current_user
from app.database.models import Alert, Kullanici
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, update, case

router = APIRouter()


# === ENUMS & SCHEMAS ===

class AlertType(str, Enum):
    FUEL_ANOMALY = "fuel_anomaly"
    COST_ANOMALY = "cost_anomaly"
    DRIVER_ALERT = "driver_alert"
    VEHICLE_ALERT = "vehicle_alert"
    SYSTEM = "system"


class AlertStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    created_at: datetime
    status: str
    source_id: Optional[int] = None
    source_type: Optional[str] = None
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertCountResponse(BaseModel):
    total: int
    unread: int
    critical: int
    high: int
    medium: int
    low: int


class AlertCreateRequest(BaseModel):
    alert_type: AlertType
    severity: str = "medium"
    title: str
    message: str
    source_id: Optional[int] = None
    source_type: Optional[str] = None


class MarkReadRequest(BaseModel):
    alert_ids: List[int]


# === ENDPOINTS ===

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    status: Optional[AlertStatus] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Tüm uyarıları getir (zil simgesi için).
    """
    stmt = select(Alert)

    if status:
        stmt = stmt.where(Alert.status == status.value)

    if severity:
        stmt = stmt.where(Alert.severity == severity)

    stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/count", response_model=AlertCountResponse)
async def get_alert_count(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Uyarı sayılarını getir (zil simgesindeki badge için).
    """
    # Optimized single query for all counts
    stmt = select(
        func.count(Alert.id).label("total"),
        func.count(case((Alert.status == 'unread', 1))).label("unread"),
        func.count(case((Alert.severity == 'critical', 1))).label("critical"),
        func.count(case((Alert.severity == 'high', 1))).label("high"),
        func.count(case((Alert.severity == 'medium', 1))).label("medium"),
        func.count(case((Alert.severity == 'low', 1))).label("low")
    )
    result = await db.execute(stmt)
    row = result.one()

    return AlertCountResponse(
        total=row.total,
        unread=row.unread,
        critical=row.critical,
        high=row.high,
        medium=row.medium,
        low=row.low
    )


@router.get("/unread", response_model=List[AlertResponse])
async def get_unread_alerts(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    limit: int = Query(10, ge=1, le=50)
):
    """
    Sadece okunmamış uyarıları getir.
    """
    stmt = select(Alert).where(
        Alert.status == 'unread'
    ).order_by(Alert.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/mark-read")
async def mark_alerts_as_read(
    request: MarkReadRequest, 
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Belirtilen uyarıları okundu olarak işaretle.
    """
    stmt = (
        update(Alert)
        .where(Alert.id.in_(request.alert_ids))
        .values(status='read', read_at=datetime.now())
    )
    result = await db.execute(stmt)
    await db.commit()

    return {"success": True, "marked_count": result.rowcount}


@router.post("/mark-all-read")
async def mark_all_alerts_as_read(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Tüm uyarıları okundu olarak işaretle.
    """
    stmt = (
        update(Alert)
        .where(Alert.status == 'unread')
        .values(status='read', read_at=datetime.now())
    )
    result = await db.execute(stmt)
    await db.commit()

    return {"success": True, "marked_count": result.rowcount}


@router.delete("/{alert_id}")
async def dismiss_alert(
    alert_id: int, 
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Uyarıyı kaldır (Soft Delete - status=dismissed).
    """
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Uyarı bulunamadı")

    # Soft delete - status dismissed olarak işaretlenir, veri korunur
    alert.status = 'dismissed'
    db.add(alert)
    await db.commit()

    return {"success": True, "dismissed_id": alert_id}


@router.post("/create", response_model=AlertResponse)
async def create_alert(
    request: AlertCreateRequest, 
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Yeni uyarı oluştur (sistem veya manuel uyarılar için).
    """
    new_alert = Alert(
        alert_type=request.alert_type.value,
        severity=request.severity,
        title=request.title,
        message=request.message,
        status='unread',
        source_id=request.source_id,
        source_type=request.source_type
    )

    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    return new_alert


@router.post("/generate-from-anomalies")
async def generate_alerts_from_anomalies(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    Anomali tespitinden otomatik uyarılar oluştur.
    Bu endpoint anomali servisini çağırarak yeni uyarılar üretir.
    """
    from app.core.services.anomaly_detector import get_anomaly_detector

    detector = get_anomaly_detector()
    anomalies = detector.get_recent_anomalies(days=7)

    created_count = 0
    for anomaly in anomalies:
        # Aynı anomali için zaten uyarı var mı kontrol et
        existing = await db.execute(
            select(Alert).where(
                Alert.source_type == anomaly.get('kaynak_tip'),
                Alert.source_id == anomaly.get('kaynak_id'),
                Alert.alert_type == 'fuel_anomaly'
            )
        )
        if existing.scalar_one_or_none():
            continue

        new_alert = Alert(
            alert_type='fuel_anomaly',
            severity=anomaly.get('severity', 'medium'),
            title=f"Anomali Tespit Edildi: {anomaly.get('tip', 'Bilinmeyen')}",
            message=anomaly.get('aciklama', ''),
            status='unread',
            source_id=anomaly.get('kaynak_id'),
            source_type=anomaly.get('kaynak_tip')
        )
        db.add(new_alert)
        created_count += 1

    if created_count > 0:
        await db.commit()

    return {"success": True, "created_count": created_count}
