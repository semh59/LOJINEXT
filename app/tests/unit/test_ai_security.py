import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.ai.qwen_chatbot import QwenChatbot, ChatMessage
from app.core.ai.prompt_tuner import PromptTuner
from app.core.ai.rag_engine import RAGEngine, SearchResult

@pytest.mark.asyncio
async def test_chatbot_input_length_limit():
    """Çok uzun mesajların reddedildiğini doğrula"""
    chatbot = QwenChatbot(load_model=False)
    chatbot.MAX_INPUT_CHARS = 10
    
    response = await chatbot.chat("Bu mesaj 10 karakterden uzun")
    assert "Mesajınız çok uzun" in response

@pytest.mark.asyncio
async def test_prompt_tuner_xml_tagging():
    """Kullanıcı sorgusunun XML tagleri ile sarmalandığını doğrula"""
    tuner = PromptTuner()
    query = "Yakıt tüketimi nedir?"
    
    prompt = tuner.build_tuned_prompt(query)
    assert "<user_input>" in prompt
    assert "</user_input>" in prompt
    assert query in prompt

@pytest.mark.asyncio
async def test_rag_similarity_threshold():
    """Düşük skorlu RAG sonuçlarının filtrelendiğini doğrula"""
    rag = RAGEngine()
    rag.is_initialized = True
    rag.SIMILARITY_THRESHOLD = 0.5
    
    # Mock search results
    mock_results = [
        SearchResult(document="İyi sonuç", metadata={}, score=0.8, source_type="trip"),
        SearchResult(document="Kötü sonuç", metadata={}, score=0.2, source_type="trip")
    ]
    
    with patch.object(rag, 'search', return_value=mock_results):
        context = await rag.search_for_context("test")
        assert "İyi sonuç" in context
        assert "Kötü sonuç" not in context

@pytest.mark.asyncio
async def test_chatbot_timeout():
    """Üretim süresi aşılırsa timeout hatası verildiğini doğrula"""
    chatbot = QwenChatbot(load_model=False)
    chatbot.model_loaded = True
    chatbot.tokenizer = MagicMock()
    chatbot.model = MagicMock()
    
    # apply_chat_template ve tokenizer çağrılarını mockla
    chatbot.tokenizer.apply_chat_template.return_value = "templated text"
    chatbot.tokenizer.return_value.to.return_value = {"input_ids": MagicMock()}
    

    with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError), \
         patch('asyncio.to_thread', side_effect=lambda *args: None):
        # chat içindeki generate_response'u çağır (history ekledik)
        response = await chatbot._generate_response("soru", "context", [], 100, 0.7)
        assert "yanıt üretimi çok uzun sürdü" in response
