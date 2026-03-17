"""
LojiNext AI - RAG (Retrieval Augmented Generation) Servisi
Uygulama verileriyle ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸renen akÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±llÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± AI sistemi

Bu servis:
1. Sefer/yakÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±t verilerinden otomatik ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸renir
2. KullanÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±cÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± sorularÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±na context-aware yanÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±t verir
3. Veri arttÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±kÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§a daha uzman hale gelir
"""

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Embedding modeli iÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§in
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
    Modernize edilmiÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ Knowledge Base.
    FAISSVectorStore kullanarak diskte kalÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±cÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± (persistent) vektÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶r depolama saÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸lar.
    JSON baÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±mlÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±lÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± kaldÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±rÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±lmÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸, yÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ksek performanslÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± yapÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±.
    """

    def __init__(self, embedding_dim: int = 384):
        self.vector_store = FAISSVectorStore(embedding_dim)
        self.model: Optional[SentenceTransformer] = None

        # Mevcut verileri yÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼kle
        if self.vector_store.load_index(str(KB_DIR)):
            logger.info("Mevcut Knowledge Base diskten yÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼klendi.")

        self._load_embedding_model()

    def _load_embedding_model(self):
        """Hafif embedding modeli yÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼kle"""
        if not EMBEDDING_AVAILABLE:
            return
        try:
            # all-MiniLM-L6-v2 (384 boyutlu, RAG Engine ile uyumlu)
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Embedding modeli yÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼klenemedi: {e}")

    def _generate_doc_id(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()[:12]

    async def add_document(
        self, content: str, category: str, metadata: Dict = None
    ) -> bool:
        """DÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶kÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼man ekle ve diske kaydet"""
        if not self.model:
            return False

        doc_id = self._generate_doc_id(content)

        # Embedding ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ret (CPU-bound)
        embedding = await asyncio.to_thread(
            self.model.encode, content, convert_to_numpy=True
        )

        metadata = metadata or {}
        metadata.update(
            {"category": category, "created_at": datetime.now(timezone.utc).isoformat()}
        )

        # FAISS'e ekle
        self.vector_store.add(doc_id, content, embedding, metadata)

        # Diske kaydet (AyrÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± bir gÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶rev olarak veya periyodik de olabilir, ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸imdilik gÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼venli olmasÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± iÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§in her eklemede)
        await asyncio.to_thread(self.vector_store.save_index, str(KB_DIR))
        return True

    async def search(
        self, query: str, top_k: int = 5, category: str = None
    ) -> List[Dict]:
        """VektÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶r arama yap"""
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
    RAG tabanlÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± akÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±llÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± AI servisi.
    Knowledge Base + LLM kombinasyonu.
    """

    def __init__(self):
        self.kb = KnowledgeBase()
        self._llm = None

    def _get_llm(self):
        """Uzak LLM istemcisi (lokal model yok)."""
        if self._llm is None:
            try:
                from app.core.ai.llm_client import get_llm_client

                self._llm = get_llm_client()
            except Exception as e:
                logger.error(f"LLM istemcisi yÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼klenemedi: {e}")
        return self._llm

    async def learn_from_trip(self, trip_data: Dict) -> bool:
        """
        Sefer verisinden ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ren (async).

        Args:
            trip_data: Sefer bilgileri (mesafe, ton, tuketim, sofor, vb.)
        """
        # Sefer ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶zetini oluÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸tur
        content = (
            f"Sefer Bilgisi: {trip_data.get('cikis_yeri', '')} ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬ÂÃ‚Â¢ {trip_data.get('varis_yeri', '')}. "
            f"Mesafe: {trip_data.get('mesafe_km', 0)} km. "
            f"YÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼k: {trip_data.get('ton', 0)} ton. "
            f"TÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ketim: {trip_data.get('tuketim', 0):.1f} L/100km. "
        )

        # Verimlilik deÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸erlendirmesi
        tuketim = trip_data.get("tuketim", 0)
        if tuketim < 28:
            content += "DeÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸erlendirme: ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¡ok verimli sefer."
        elif tuketim > 38:
            content += "DeÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸erlendirme: YÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ksek tÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ketim, incelenmeli."
        else:
            content += "DeÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸erlendirme: Normal sefer."

        return await self.kb.add_document(content, category="sefer", metadata=trip_data)

    async def learn_from_fuel(self, fuel_data: Dict) -> bool:
        """YakÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±t verisinden ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ren (async)"""
        content = (
            f"YakÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±t AlÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±mÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±: {fuel_data.get('litre', 0):.1f} litre, "
            f"Fiyat: {fuel_data.get('fiyat_tl', 0):.2f} TL/L, "
            f"ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â°stasyon: {fuel_data.get('istasyon', 'Bilinmiyor')}. "
            f"KM SayaÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§: {fuel_data.get('km_sayac', 0)}."
        )

        return await self.kb.add_document(content, category="yakit", metadata=fuel_data)

    async def learn_from_log(self, log_entry: Dict) -> bool:
        """Sistem logundan ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ren (async)"""
        timestamp = log_entry.get("timestamp", datetime.now(timezone.utc).isoformat())
        level = log_entry.get("level", "INFO")
        msg = log_entry.get("message", "")
        module = log_entry.get("module", "unknown")

        content = f"Sistem Logu [{level}]: {msg} (Zaman: {timestamp}, ModÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼l: {module})"

        return await self.kb.add_document(
            content, category="log", metadata={"level": level, "module": module}
        )

    async def learn_from_event(self, event_type: str, details: Dict) -> bool:
        """Sistem olayÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â±ndan ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ren (async)"""
        content = (
            f"Sistem OlayÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â± [{event_type}]: {json.dumps(details, ensure_ascii=False)}"
        )

        return await self.kb.add_document(
            content, category="event", metadata={"event_type": event_type}
        )

    async def teach(self, knowledge: str, category: str = "genel") -> bool:
        """
        Manuel bilgi ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ret (async).

        Args:
            knowledge: ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸retilecek bilgi
            category: Kategori
        """
        return await self.kb.add_document(knowledge, category=category)

    async def ask(self, question: str, use_context: bool = True) -> Dict:
        """
        AkÃ„Â±llÃ„Â± soru-cevap (async).

        Args:
            question: KullanÃ„Â±cÃ„Â± sorusu
            use_context: Knowledge base context'i kullan

        Returns:
            YanÃ„Â±t ve kullanÃ„Â±lan kaynaklar
        """
        context = ""
        sources = []

        if use_context:
            relevant_docs = await self.kb.search(question, top_k=3)
            if relevant_docs:
                context = "Ã„Â°lgili Bilgiler:\n"
                for doc in relevant_docs:
                    context += f"- {doc['content']}\n"
                    sources.append({"id": doc["id"], "category": doc["category"], "score": doc["score"]})
                    sources.append({"id": doc["id"], "category": doc["category"], "score": doc["score"]})

        llm = self._get_llm()
        if llm:
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": question})
            response = await llm.chat(
                messages=messages,
                max_tokens=512,
                temperature=0.3,
                system_prompt="Sen bir TIR yakÃ„Â±t ve lojistik uzmansÃ„Â±n. Context varsa zorunlu kullan, TÃƒÂ¼rkÃƒÂ§e ve kÃ„Â±sa yanÃ„Â±t ver.",
            )
        else:
            response = "AI istemcisi kullanÃ„Â±lamÃ„Â±yor. LÃƒÂ¼tfen LLM API anahtarÃ„Â±nÃ„Â± kontrol et."

        return {"answer": response, "sources": sources, "context_used": bool(context)}

    def get_stats(self) -> Dict:
        """Ãƒâ€“Ã„Å¸renme istatistikleri"""
        kb_stats = self.kb.get_stats()

        llm = self._get_llm()
        llm_status = "available" if llm else "unavailable"

        return {
            "knowledge_base": kb_stats,
            "llm_status": llm_status,
            "embedding_model": "all-MiniLM-L6-v2" if self.kb.model else "unavailable",
        }

def get_smart_ai() -> SmartAIService:
    from app.core.container import get_container

    return get_container().smart_ai_service
