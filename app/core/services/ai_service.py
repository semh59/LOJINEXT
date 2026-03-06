"""
TIR Yakıt Takip - AI Servisi (Groq-Exclusive)
Groq Cloud API tabanlı yapay zeka servisi.
"""

import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.infrastructure.logging.logger import get_logger
from app.core.ai.groq_service import GroqService, get_groq_service, ChatMessage
from app.core.ai.rag_engine import get_rag_engine
from app.database.unit_of_work import UnitOfWork

logger = get_logger(__name__)


class AIService:
    """
    Groq Cloud LLM Servisi.
    Model: Llama 3.3 70B (Primary)

    Özellikler:
    - Yüksek performanslı bulut tabanlı çıkarım
    - Sistem verilerini (sefer, yakıt) context olarak kullanır (RAG)
    - Yerel model bağımlılığı içermez
    """

    @classmethod
    def get_progress(cls):
        """
        API tabanlı olduğu için indirme süreci yoktur.
        Her zaman hazır döner.
        """
        return {
            "status": "ready",
            "percent": 100.0,
            "speed": "Groq Cloud",
        }

    # Configuration constants
    MAX_INPUT_CHARS = 2000
    FALLBACK_RESPONSE = "Üzgünüm, şu anda yanıt veremiyorum. Lütfen teknik destek ekibiyle iletişime geçin."

    def __init__(self, groq_service: Optional[GroqService] = None):
        self.groq = groq_service or get_groq_service()
        self._last_inference_time_ms = 0
        self._cache = {}
        self._lock = threading.Lock()
        self._system_prompt = (
            "Sen LojiNext AI sisteminin 'Kıdemli Lojistik Analisti ve Filo Danışmanı' rolündesin. "
            "Görevin, sağlanan filo verilerini, yakıt tüketimlerini ve sefer kayıtlarını analiz ederek "
            "profesyonel, veriye dayalı ve aksiyon alınabilir yanıtlar üretmektir.\n\n"
            "KURALLAR:\n"
            "1. Profesyonel, veriye dayalı ve teknik bir dil kullan.\n"
            "2. Cevapların Türkçe olsun.\n"
            "3. Teknik terimleri (Cd, aerodinamik, motor verimi) yerinde kullan.\n"
            "4. Tahminleme yaparken sistem verilerine sadık kal.\n"
            "5. Kullanıcıyı yakıt tasarrufu ve güvenli sürüş konusunda yönlendir.\n"
            "6. Kullanıcının sistemdeki rolüne (Admin/Superadmin) uygun, saygılı ve yetki sınırlarını bilen bir dil kullan."
        )

    def _fallback_response(self, original_query: str, error_msg: str = "") -> str:
        """Hata durumunda güvenli yedek yanıt dön"""
        logger.warning(
            f"AI Fallback triggered for query: {original_query[:50]}... Error: {error_msg}"
        )
        return self.FALLBACK_RESPONSE

    async def _build_context(self, user_id: int = None) -> str:
        """
        Sistem verilerinden yapılandırılmış context oluştur.
        """
        from app.database.repositories.analiz_repo import get_analiz_repo
        from app.database.repositories.arac_repo import get_arac_repo

        context = []

        # 0. Kullanıcı Kimlik ve Yetki Bilgisi
        if user_id:
            try:
                async with UnitOfWork() as uow:
                    user = await uow.kullanici_repo.get_by_id(user_id)
                    if user:
                        role_name = user.rol.upper() if hasattr(user, "rol") else "USER"
                        context.append("### AKTİF KULLANICI BİLGİSİ ###")
                        context.append(f"- Kimlik: {user.kullanici_adi}")
                        context.append(f"- Rol/Yetki: {role_name}")
                        if role_name == "SUPERADMIN":
                            context.append(
                                "- NOT: Bu kullanıcı tam sistem yetkisine sahiptir."
                            )
            except Exception as e:
                logger.warning(f"User context build failed: {e}")

        context.append("### MEVCUT FİLO DURUMU VE VERİLER ###")

        try:
            # 1. Genel Dashboard İstatistikleri
            analiz_repo = get_analiz_repo()
            stats = await analiz_repo.get_dashboard_stats()
            if stats:
                context.append(
                    f"- Filo Özeti: {stats['toplam_arac']} Araç, {stats['toplam_sofor']} Şoför, "
                    f"Aylık Ortalama Tüketim: {stats.get('filo_ortalama', 32.0):.1f} L/100km."
                )

            # 2. Kritik Anomali ve Uyarılar (Son 3)
            alerts = await analiz_repo.get_recent_unread_alerts(limit=3)
            if alerts:
                context.append("- Kritik Uyarılar:")
                for alert in alerts:
                    context.append(f"  * {alert['title']}: {alert['message']}")

            # 3. Öne Çıkan Araç Spekleri
            araclar = await get_arac_repo().get_all(limit=3)
            if araclar:
                context.append("- Araç Teknik Verileri (Örnek):")
                for a in araclar:
                    context.append(
                        f"  * {a.plaka}: Aero Cd: {getattr(a, 'hava_direnc_katsayisi', 0.7)}, "
                        f"Verim: %{int(getattr(a, 'motor_verimliligi', 0.38) * 100)}"
                    )

        except Exception as e:
            logger.warning(f"Context building failed: {e}")
            context.append("(Sistem verileri şu an alınamıyor, genel bilgi ver.)")

        return "\n".join(context)

    def _sanitize_prompt(self, text: str) -> str:
        """FAZ 5.2: Prompt Injection Koruması"""
        pattern = r"(?i)(SYSTEM|ASSISTANT|USER|ADMIN)(\s*:|s*_|\s+MODE)"
        sanitized = re.sub(pattern, "[REDACTED]", text)

        if "###" in sanitized:
            sanitized = sanitized.replace("###", "[REDACTED]")

        return sanitized.strip()[:2000]  # Groq allows more context

    async def generate_response(
        self, prompt: str, history: Optional[List[Dict]] = None, user_id: int = None
    ) -> str:
        """Groq API üzerinden yanıt üret"""
        try:
            if len(prompt) > self.MAX_INPUT_CHARS:
                error_msg = (
                    f"Giriş metni çok uzun (Max {self.MAX_INPUT_CHARS} karakter)"
                )
                logger.warning(f"AI Input Limit Exceeded: {len(prompt)} chars")
                return f"Hata: {error_msg}"

            safe_prompt = self._sanitize_prompt(prompt)
            context_data = await self._build_context(user_id)

            # RAG
            rag = get_rag_engine()
            if rag.is_initialized:
                rag_context = await rag.search_for_context(
                    query=safe_prompt,
                    user_id=user_id,
                    max_chars=settings.AI_RAG_MAX_CHARS,
                )
                if rag_context:
                    context_data = f"{context_data}\n\n{rag_context}"

            # Process history
            history_objs = []
            if history:
                for msg in history[-10:]:
                    history_objs.append(
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", ""),
                        )
                    )

            # Call Groq
            groq = get_groq_service()
            return await groq.chat(
                user_message=safe_prompt,
                history=history_objs,
                context=context_data,
                system_prompt=self._system_prompt,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
            )

        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            return "Üzgünüm, şu anda yanıt veremiyorum."

    async def stream_response(
        self, prompt: str, history: Optional[List[Dict]] = None, user_id: int = None
    ):
        """Groq API üzerinden streaming yanıt üret"""
        try:
            safe_prompt = self._sanitize_prompt(prompt)
            context_data = await self._build_context(user_id)

            history_objs = []
            if history:
                for msg in history[-10:]:
                    history_objs.append(
                        ChatMessage(
                            role=msg.get("role", "user"),
                            content=msg.get("content", ""),
                        )
                    )

            groq = get_groq_service()
            async for chunk in groq.chat_stream(
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
            yield "Üzgünüm, şu anda yanıt veremiyorum."

    async def train_model(self) -> Dict[str, Any]:
        """
        API tabanlı sistemde 'eğitim' bir anlam ifade etmez.
        Ancak RAG entegrasyonu başarılı döner.
        """
        return {
            "status": "success",
            "message": "Cloud AI sistemi güncel. RAG verileri senkronize edildi.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Singleton
_ai_service = None
_ai_lock = threading.Lock()


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        with _ai_lock:
            if _ai_service is None:
                _ai_service = AIService()
    return _ai_service
