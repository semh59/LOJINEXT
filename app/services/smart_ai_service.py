"""
LojiNext AI - RAG (Retrieval Augmented Generation) Servisi
Uygulama verileriyle öğrenen akıllı AI sistemi

Bu servis:
1. Sefer/yakıt verilerinden otomatik öğrenir
2. Kullanıcı sorularına context-aware yanıt verir
3. Veri arttıkça daha uzman hale gelir
"""

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Embedding modeli için
try:
    from sentence_transformers import SentenceTransformer

    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

from app.core.ai.rag_engine import FAISSVectorStore

# Knowledge Base dizini
KB_DIR = Path(__file__).parent.parent.parent / "data" / "ai_kb"
KB_DIR.mkdir(parents=True, exist_ok=True)


class KnowledgeBase:
    """
    Modernize edilmiş Knowledge Base.
    FAISSVectorStore kullanarak diskte kalıcı (persistent) vektör depolama sağlar.
    JSON bağımlılığı kaldırılmış, yüksek performanslı yapı.
    """

    def __init__(self, embedding_dim: int = 384):
        self.vector_store = FAISSVectorStore(embedding_dim)
        self.model: Optional[SentenceTransformer] = None

        # Mevcut verileri yükle
        if self.vector_store.load_index(str(KB_DIR)):
            logger.info("Mevcut Knowledge Base diskten yüklendi.")

        self._load_embedding_model()

    def _load_embedding_model(self):
        """Hafif embedding modeli yükle"""
        if not EMBEDDING_AVAILABLE:
            return
        try:
            # all-MiniLM-L6-v2 (384 boyutlu, RAG Engine ile uyumlu)
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Embedding modeli yüklenemedi: {e}")

    def _generate_doc_id(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()[:12]

    async def add_document(
        self, content: str, category: str, metadata: Dict = None
    ) -> bool:
        """Döküman ekle ve diske kaydet"""
        if not self.model:
            return False

        doc_id = self._generate_doc_id(content)

        # Embedding üret (CPU-bound)
        embedding = await asyncio.to_thread(
            self.model.encode, content, convert_to_numpy=True
        )

        metadata = metadata or {}
        metadata.update(
            {"category": category, "created_at": datetime.now(timezone.utc).isoformat()}
        )

        # FAISS'e ekle
        self.vector_store.add(doc_id, content, embedding, metadata)

        # Diske kaydet (Ayrı bir görev olarak veya periyodik de olabilir, şimdilik güvenli olması için her eklemede)
        await asyncio.to_thread(self.vector_store.save_index, str(KB_DIR))
        return True

    async def search(
        self, query: str, top_k: int = 5, category: str = None
    ) -> List[Dict]:
        """Vektör arama yap"""
        if not self.model or self.vector_store.count() == 0:
            return []

        query_embedding = await asyncio.to_thread(
            self.model.encode, query, convert_to_numpy=True
        )

        # Kategori filtresi
        source_types = [category] if category else None

        # Search returns List[tuple(idx, score)]
        raw_results = await asyncio.to_thread(
            self.vector_store.search, query_embedding, top_k, source_types
        )

        results = []
        for idx, score in raw_results:
            if score > 0.3:
                results.append(
                    {
                        "id": self.vector_store.idx_to_doc_id.get(idx),
                        "content": self.vector_store.documents.get(idx),
                        "category": self.vector_store.metadatas.get(idx, {}).get(
                            "category"
                        ),
                        "metadata": self.vector_store.metadatas.get(idx),
                        "score": float(score),
                    }
                )
        return results

    def get_stats(self) -> Dict:
        return {
            "total_documents": self.vector_store.count(),
            "storage_path": str(KB_DIR),
            "initialized": self.model is not None,
        }


class SmartAIService:
    """
    RAG tabanlı akıllı AI servisi.
    Knowledge Base + LLM kombinasyonu.
    """

    def __init__(self):
        self.kb = KnowledgeBase()
        self._llm = None

    def _get_llm(self):
        """LLM'i lazy load et"""
        if self._llm is None:
            try:
                from app.services.ai_service import LocalAIService

                self._llm = LocalAIService()
            except Exception as e:
                logger.error(f"LLM yüklenemedi: {e}")
        return self._llm

    async def learn_from_trip(self, trip_data: Dict) -> bool:
        """
        Sefer verisinden öğren (async).

        Args:
            trip_data: Sefer bilgileri (mesafe, ton, tuketim, sofor, vb.)
        """
        # Sefer özetini oluştur
        content = (
            f"Sefer Bilgisi: {trip_data.get('cikis_yeri', '')} → {trip_data.get('varis_yeri', '')}. "
            f"Mesafe: {trip_data.get('mesafe_km', 0)} km. "
            f"Yük: {trip_data.get('ton', 0)} ton. "
            f"Tüketim: {trip_data.get('tuketim', 0):.1f} L/100km. "
        )

        # Verimlilik değerlendirmesi
        tuketim = trip_data.get("tuketim", 0)
        if tuketim < 28:
            content += "Değerlendirme: Çok verimli sefer."
        elif tuketim > 38:
            content += "Değerlendirme: Yüksek tüketim, incelenmeli."
        else:
            content += "Değerlendirme: Normal sefer."

        return await self.kb.add_document(content, category="sefer", metadata=trip_data)

    async def learn_from_fuel(self, fuel_data: Dict) -> bool:
        """Yakıt verisinden öğren (async)"""
        content = (
            f"Yakıt Alımı: {fuel_data.get('litre', 0):.1f} litre, "
            f"Fiyat: {fuel_data.get('fiyat_tl', 0):.2f} TL/L, "
            f"İstasyon: {fuel_data.get('istasyon', 'Bilinmiyor')}. "
            f"KM Sayaç: {fuel_data.get('km_sayac', 0)}."
        )

        return await self.kb.add_document(content, category="yakit", metadata=fuel_data)

    async def learn_from_log(self, log_entry: Dict) -> bool:
        """Sistem logundan öğren (async)"""
        timestamp = log_entry.get("timestamp", datetime.now(timezone.utc).isoformat())
        level = log_entry.get("level", "INFO")
        msg = log_entry.get("message", "")
        module = log_entry.get("module", "unknown")

        content = f"Sistem Logu [{level}]: {msg} (Zaman: {timestamp}, Modül: {module})"

        return await self.kb.add_document(
            content, category="log", metadata={"level": level, "module": module}
        )

    async def learn_from_event(self, event_type: str, details: Dict) -> bool:
        """Sistem olayından öğren (async)"""
        content = (
            f"Sistem Olayı [{event_type}]: {json.dumps(details, ensure_ascii=False)}"
        )

        return await self.kb.add_document(
            content, category="event", metadata={"event_type": event_type}
        )

    async def teach(self, knowledge: str, category: str = "genel") -> bool:
        """
        Manuel bilgi öğret (async).

        Args:
            knowledge: Öğretilecek bilgi
            category: Kategori
        """
        return await self.kb.add_document(knowledge, category=category)

    async def ask(self, question: str, use_context: bool = True) -> Dict:
        """
        Akıllı soru-cevap (async).

        Args:
            question: Kullanıcı sorusu
            use_context: Knowledge base context'i kullan

        Returns:
            Yanıt ve kullanılan kaynaklar
        """
        context = ""
        sources = []

        # Knowledge base'den ilgili bilgileri al
        if use_context:
            relevant_docs = await self.kb.search(question, top_k=3)
            if relevant_docs:
                context = "İlgili Bilgiler:\n"
                for doc in relevant_docs:
                    context += f"- {doc['content']}\n"
                    sources.append(
                        {
                            "id": doc["id"],
                            "category": doc["category"],
                            "score": doc["score"],
                        }
                    )

        # LLM ile yanıt üret
        llm = self._get_llm()
        if llm and llm._model:
            prompt = f"{context}\n\nSoru: {question}\n\nYanıt:"
            response = await llm.generate_response(
                prompt,
                system_prompt="Sen bir TIR yakıt ve lojistik uzmanısın. Verilen context'i kullanarak kısa ve öz yanıtlar ver. Türkçe yanıt ver.",
            )
        else:
            response = "AI modeli yüklü değil. Lütfen model kurulumunu tamamlayın."

        return {"answer": response, "sources": sources, "context_used": bool(context)}

    def get_stats(self) -> Dict:
        """Öğrenme istatistikleri"""
        kb_stats = self.kb.get_stats()

        llm = self._get_llm()
        llm_status = "available" if (llm and llm._model) else "unavailable"

        return {
            "knowledge_base": kb_stats,
            "llm_status": llm_status,
            "embedding_model": "all-MiniLM-L6-v2" if self.kb.model else "unavailable",
        }


def get_smart_ai() -> SmartAIService:
    from app.core.container import get_container

    return get_container().smart_ai_service
