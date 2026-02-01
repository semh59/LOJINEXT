from typing import Annotated
from fastapi import APIRouter, Depends
from app.api.deps import SessionDep, get_current_user
from app.database.models import Kullanici
from app.core.services.ai_service import AIService

router = APIRouter()

@router.get("/progress")
async def get_ai_model_progress(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    AI Model durumunu döndürür.
    """
    return AIService.get_progress()

@router.get("/status")
async def get_ai_status(
    db: SessionDep,
    current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """AI sisteminin genel durumunu döner."""
    progress = AIService.get_progress()
    return {
        "is_ready": progress["status"] == "ready",
        "progress": progress
    }
