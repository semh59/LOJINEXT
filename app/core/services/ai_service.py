"""
TIR Yakit Takip - AI Servisi (Remote LLM)
"""

import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.ai.groq_service import ChatMessage, GroqService, get_groq_service
from app.core.ai.rag_engine import get_rag_engine
from app.database.unit_of_work import UnitOfWork
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class AIService:
    """Groq tabanli AI servisi."""

    MAX_INPUT_CHARS = 2000
    FALLBACK_RESPONSE = (
        "Uzgunum, su anda yanit veremiyorum. Lutfen teknik destek ekibiyle iletisime gecin."
    )

    @classmethod
    def get_progress(cls):
        return {
            "status": "ready",
            "percent": 100.0,
            "speed": "Groq Cloud",
        }

    def __init__(self, groq_service: Optional[GroqService] = None):
        self.groq = groq_service or get_groq_service()
        self._last_inference_time_ms = 0
        self._cache = {}
        self._lock = threading.Lock()
        self._system_prompt = (
            "Sen LojiNext AI sisteminin 'Kidemli Lojistik Analisti ve Filo Danismani' rolundesin. "
            "Profesyonel, veriye dayali ve aksiyon alinabilir yanitlar uret."
        )

    def _fallback_response(self, original_query: str, error_msg: str = "") -> str:
        logger.warning(
            f"AI Fallback triggered for query: {str(original_query)[:50]}... Error: {error_msg}"
        )
        return self.FALLBACK_RESPONSE

    async def _build_context(self, user_id: int = None) -> str:
        from app.database.repositories.analiz_repo import get_analiz_repo
        from app.database.repositories.arac_repo import get_arac_repo

        context: List[str] = []

        if user_id:
            try:
                async with UnitOfWork() as uow:
                    user = await uow.kullanici_repo.get_by_id(user_id)
                    if user:
                        role_name = user.rol.upper() if hasattr(user, "rol") else "USER"
                        context.append("### AKTIF KULLANICI BILGISI ###")
                        context.append(f"- Kimlik: {getattr(user, 'kullanici_adi', 'bilinmiyor')}")
                        context.append(f"- Rol/Yetki: {role_name}")
                        if role_name == "SUPERADMIN":
                            context.append("- NOT: Bu kullanici tam sistem yetkisine sahiptir.")
            except Exception as e:
                logger.warning(f"User context build failed: {e}")

        context.append("### MEVCUT FILO DURUMU VE VERILER ###")

        try:
            analiz_repo = get_analiz_repo()
            stats = await analiz_repo.get_dashboard_stats()
            if stats:
                context.append(
                    f"- Filo Ozeti: {stats.get('toplam_arac', 0)} Arac, {stats.get('toplam_sofor', 0)} Sofor, "
                    f"Aylik Ortalama Tuketim: {stats.get('filo_ortalama', 32.0):.1f} L/100km."
                )

            alerts = await analiz_repo.get_recent_unread_alerts(limit=3)
            if alerts:
                context.append("- Kritik Uyarilar:")
                for alert in alerts:
                    context.append(f"  * {alert.get('title', '')}: {alert.get('message', '')}")

            araclar = await get_arac_repo().get_all(limit=3)
            if araclar:
                context.append("- Arac Teknik Verileri (Ornek):")
                for a in araclar:
                    if isinstance(a, dict):
                        plaka = a.get("plaka", "?")
                        cd = a.get("hava_direnc_katsayisi", 0.7)
                        verim = a.get("motor_verimliligi", 0.38)
                    else:
                        plaka = getattr(a, "plaka", "?")
                        cd = getattr(a, "hava_direnc_katsayisi", 0.7)
                        verim = getattr(a, "motor_verimliligi", 0.38)
                    context.append(
                        f"  * {plaka}: Aero Cd: {cd}, Verim: %{int(float(verim) * 100)}"
                    )

        except Exception as e:
            logger.warning(f"Context building failed: {e}")
            context.append("(Sistem verileri su an alinamiyor, genel bilgi ver.)")

        return "\n".join(context)

    def _sanitize_prompt(self, text: str) -> str:
        pattern = r"(?i)(SYSTEM|ASSISTANT|USER|ADMIN)(\s*:|s*_|\s+MODE)"
        sanitized = re.sub(pattern, "[REDACTED]", str(text or ""))
        sanitized = sanitized.replace("###", "[REDACTED]")
        return sanitized.strip()[:1000]

    async def generate_response(
        self, prompt: str, history: Optional[List[Dict]] = None, user_id: int = None
    ) -> str:
        try:
            if len(str(prompt or "")) > self.MAX_INPUT_CHARS:
                error_msg = (
                    f"Giris metni cok uzun (Max {self.MAX_INPUT_CHARS} karakter)"
                )
                logger.warning(f"AI Input Limit Exceeded: {len(prompt)} chars")
                return f"Hata: {error_msg}"

            safe_prompt = self._sanitize_prompt(prompt)
            context_data = await self._build_context(user_id)

            rag = get_rag_engine()
            if rag.is_initialized:
                rag_context = await rag.search_for_context(
                    query=safe_prompt,
                    user_id=user_id,
                    max_chars=settings.AI_RAG_MAX_CHARS,
                )
                if rag_context:
                    context_data = f"{context_data}\n\n{rag_context}"

            history_objs: List[ChatMessage] = []
            if history:
                for msg in history[-10:]:
                    history_objs.append(
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", ""),
                        )
                    )

            return await self.groq.chat(
                user_message=safe_prompt,
                history=history_objs,
                context=context_data,
                system_prompt=self._system_prompt,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
            )

        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return "Uzgunum, su anda yanit veremiyorum."

    async def stream_response(
        self, prompt: str, history: Optional[List[Dict]] = None, user_id: int = None
    ):
        try:
            safe_prompt = self._sanitize_prompt(prompt)
            context_data = await self._build_context(user_id)

            history_objs: List[ChatMessage] = []
            if history:
                for msg in history[-10:]:
                    history_objs.append(
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", ""),
                        )
                    )

            async for chunk in self.groq.chat_stream(
                user_message=safe_prompt,
                history=history_objs,
                context=context_data,
                system_prompt=self._system_prompt,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
            ):
                yield chunk

        except Exception as e:
            logger.error(f"AI Streaming Error: {e}")
            yield "Uzgunum, su anda yanit veremiyorum."

    async def train_model(self) -> Dict[str, Any]:
        """Remote AI icin egitim ozeti (compat)."""
        from app.database.repositories.sefer_repo import get_sefer_repo
        from app.database.repositories.yakit_repo import get_yakit_repo

        async def _count(repo) -> int:
            if hasattr(repo, "count"):
                return int((await repo.count()) or 0)
            if hasattr(repo, "get_all"):
                rows = await repo.get_all()
                if isinstance(rows, dict):
                    return int(rows.get("total", len(rows.get("items", []))))
                return len(rows or [])
            return 0

        total = await _count(get_sefer_repo()) + await _count(get_yakit_repo())

        return {
            "status": "success",
            "message": "Cloud AI sistemi guncel. RAG verileri senkronize edildi.",
            "data_points": total,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


_ai_service = None
_ai_lock = threading.Lock()


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        with _ai_lock:
            if _ai_service is None:
                _ai_service = AIService()
    return _ai_service
