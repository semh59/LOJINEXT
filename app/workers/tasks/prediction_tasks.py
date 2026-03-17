"""
Prediction task (async) - RAG + LLM çağrısı.
Sonuçlar Celery backend + opsiyonel Redis cache'te tutulur.
"""

import asyncio
from datetime import datetime, timezone

import json
import redis

from app.infrastructure.background.celery_app import celery_app
from app.core.ai.llm_client import get_llm_client, LLMMessage
from app.core.ai.rag_engine import FAISSVectorStore
from app.database.connection import AsyncSessionLocal
from app.database.models import PredictionResult


@celery_app.task(bind=True, name="prediction.generate", max_retries=3, acks_late=True)
def run_prediction_task(self, question: str, context: str | None = None) -> dict:
    """
    Basit RAG+LLM task'ı (bloklayan).
    Dönen dict JSON-serileştirilebilir olmalı.
    """
    loop = asyncio.get_event_loop()
    llm = get_llm_client()

    async def _run():
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": question})
        answer = await llm.chat(
            messages=[LLMMessage(**m) for m in messages],
            max_tokens=512,
            temperature=0.3,
            system_prompt="Sen bir TIR yakıt ve lojistik uzmansın. Kısa, Türkçe yanıt ver.",
        )
        return answer

    redis_client = redis.Redis.from_url(celery_app.conf.broker_url)
    cache_key = f"pred:result:{self.request.id}"

    # Idempotency: önceden tamamlanmışsa cache'den dön
    try:
        if redis_client.exists(cache_key):
            cached = json.loads(redis_client.get(cache_key))
            return cached
    except Exception:
        pass

    try:
        answer = loop.run_until_complete(_run())
        result_payload = {
            "status": "completed",
            "answer": answer,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        loop.run_until_complete(_persist(task_id=self.request.id, status="success", answer=answer))
        try:
            redis_client.setex(cache_key, 86400, json.dumps(result_payload))
        except Exception:
            pass
        return result_payload
    except Exception as exc:
        try:
            self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            loop.run_until_complete(_persist(task_id=self.request.id, status="failed", error=str(exc)))
            try:
                redis_client.lpush(
                    "pred:dlq",
                    json.dumps(
                        {
                            "task_id": self.request.id,
                            "status": "failed",
                            "error": str(exc),
                            "failed_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                )
            except Exception:
                pass
            return {
                "status": "failed",
                "error": str(exc),
                "failed_at": datetime.now(timezone.utc).isoformat(),
            }


async def _persist(task_id: str, status: str, answer: str | None = None, error: str | None = None):
    """Sonucu prediction_results tablosuna yazar (best-effort)."""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(PredictionResult).where(PredictionResult.task_id == task_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                existing = PredictionResult(task_id=task_id)
                session.add(existing)
            existing.status = status
            existing.answer = answer
            existing.error = error
            existing.finished_at = datetime.now(timezone.utc)
            await session.commit()
    except Exception:
        # DB yazımı opsiyonel; hata durumunda sessiz geç
        pass
