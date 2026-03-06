from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.services.notification_service import NotificationService
from app.infrastructure.security.permission_checker import require_yetki
from app.api.deps import get_current_user
from app.database.models import Kullanici
from pydantic import BaseModel

router = APIRouter()


class NotificationRuleCreate(BaseModel):
    olay_tipi: str
    kanallar: List[str]
    alici_rol_id: int
    aktif: bool = True


@router.get(
    "/rules", dependencies=[Depends(require_yetki("notification_rule_goruntule"))]
)
async def list_rules():
    """Admin: List all notification rules."""
    from app.database.unit_of_work import UnitOfWork

    async with UnitOfWork() as uow:
        return await uow.notification_repo.get_all_rules()


@router.post(
    "/rules",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_yetki(["notification_rule_ekle", "all", "*"]))],
)
async def create_rule(data: NotificationRuleCreate):
    """Admin: Create a new notification rule."""
    from app.database.unit_of_work import UnitOfWork

    async with UnitOfWork() as uow:
        rule = await uow.notification_repo.create_rule(data.model_dump())
        await uow.commit()
        return rule


@router.get("/my")
async def get_my_notifications(current_user: Kullanici = Depends(get_current_user)):
    """User: Get notifications for the logged-in user."""
    service = NotificationService()
    notifications = await service.get_user_notifications(current_user.id)
    # Convert to frontend-friendly format
    return [
        {
            "id": n.id,
            "baslik": n.baslik,
            "icerik": n.icerik,
            "olay_tipi": n.olay_tipi,
            "kanal": n.kanal,
            "durum": n.durum,
            "okundu": n.durum == "READ",
            "olusturma_tarihi": n.olusturma_tarihi.isoformat(),
        }
        for n in notifications
    ]


@router.post("/mark-all-read")
async def mark_all_read(current_user: Kullanici = Depends(get_current_user)):
    """User: Mark all notifications as read."""
    service = NotificationService()
    count = await service.mark_all_as_read(current_user.id)
    return {"success": True, "count": count}


@router.patch("/{notification_id}/read")
async def mark_single_read(
    notification_id: int, current_user: Kullanici = Depends(get_current_user)
):
    """User: Mark a notification as read."""
    service = NotificationService()
    success = await service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bildirim bulunamadı.")
    return {"success": True}
