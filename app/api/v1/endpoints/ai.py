from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, get_current_user
from app.core.services.ai_service import AIService, get_ai_service
from app.database.models import Kullanici

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., example="Filo durumu nedir?")
    history: Optional[List[dict]] = Field(
        default=[], example=[{"role": "user", "content": "Selam"}]
    )


@router.get("/progress")
async def get_ai_model_progress(
    db: SessionDep, current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    AI Model durumunu döndürür.
    """
    return AIService.get_progress()


@router.get("/status")
async def get_ai_status(
    db: SessionDep, current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """AI sisteminin genel durumunu döner."""
    progress = AIService.get_progress()
    return {"is_ready": progress["status"] == "ready", "progress": progress}


@router.post("/chat")
async def chat_with_ai(
    request: ChatRequest, current_user: Annotated[Kullanici, Depends(get_current_user)]
):
    """
    AIService üzerinden RAG destekli sohbet et.
    """
    ai_service = get_ai_service()

    # Generate response via AIService (which handles context/RAG and history)
    response = await ai_service.generate_response(
        prompt=request.message, history=request.history, user_id=current_user.id
    )

    return {"response": response, "timestamp": datetime.now(timezone.utc).isoformat()}
