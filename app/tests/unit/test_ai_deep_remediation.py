import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.ai.rag_engine import get_rag_engine
from app.core.ai.qwen_chatbot import get_chatbot, _chatbot
from app.core.services.anomaly_detector import AnomalyDetector, AnomalyResult, AnomalyType, SeverityEnum

@pytest.mark.asyncio
async def test_rag_engine_regression_fixed():
    """EMBEDDING_MODEL özniteliğinin varlığını doğrula (Regression Test)"""
    rag = get_rag_engine()
    assert hasattr(rag, 'EMBEDDING_MODEL')
    assert rag.EMBEDDING_MODEL is not None

@pytest.mark.asyncio
async def test_chatbot_singleton_reload():
    """Singleton chatbot'un çalışma zamanında model yükleyebildiğini doğrula"""
    # Önce model yüklemeden al
    with patch('app.core.ai.qwen_chatbot._chatbot', None):
        cb = get_chatbot(load_model=False)
        assert cb.model_loaded is False
        
        # Sonra model yükleyerek al
        with patch.object(cb, '_load_model') as mock_load:
            # model_loaded check'ini geçmesi için False kalmalı
            get_chatbot(load_model=True)
            mock_load.assert_called_once()

@pytest.mark.asyncio
async def test_anomaly_bulk_insert():
    """Bulk insert mantığının SQL çağrısını doğrula"""
    detector = AnomalyDetector()
    anomalies = [
        AnomalyResult(AnomalyType.TUKETIM, 'arac', 1, 35.0, 32.0, 9.3, SeverityEnum.LOW, 'test1'),
        AnomalyResult(AnomalyType.TUKETIM, 'arac', 2, 45.0, 32.0, 40.6, SeverityEnum.HIGH, 'test2')
    ]
    
    with patch('app.core.services.anomaly_detector.get_uow') as mock_uow:
        # Async context manager mock'la
        uow_instance = MagicMock()
        uow_instance.session.execute = AsyncMock()
        uow_instance.commit = AsyncMock()
        mock_uow.return_value.__aenter__.return_value = uow_instance
        
        await detector.save_anomalies(anomalies)
        
        # execute'un çağrıldığını ve params_list'in geçtiğini doğrula
        args, kwargs = uow_instance.session.execute.call_args
        assert len(args[1]) == 2 # 2 elemanlı liste geçmiş olmalı
        assert args[1][0]['kaynak_id'] == 1
        assert args[1][1]['kaynak_id'] == 2

@pytest.mark.asyncio
async def test_recommendation_cache_thread_safety():
    """Cache lock'unun varlığını doğrula"""
    from app.core.ai.recommendation_engine import get_recommendation_engine
    engine = get_recommendation_engine()
    assert hasattr(engine, '_lock')
    assert engine._lock is not None
