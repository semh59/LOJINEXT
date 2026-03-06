"""
Servis Katmanı Audit - FAZ 3 Kapsamlı Test Suite
Tüm düzeltmelerin detaylı testleri

Kapsam:
- FAZ 1: SQL Injection, Singleton, Circuit Breaker, Audit Logger
- FAZ 2: URL Bypass, Thread Safety, Import Validation, Correlation ID
"""
import pytest
import asyncio


# ============================================================================
# FAZ 2 KRİTİK TESTLER
# ============================================================================

class TestURLBypassFix:
    """Model URL Bypass düzeltmesi testleri - Kritik 1"""
    
    def test_subdomain_spoofing_blocked(self):
        """Subdomain spoofing saldırıları engellenmeli"""
        from app.services.ai_service import LocalAIService
        
        service = LocalAIService.__new__(LocalAIService)
        
        # Subdomain spoofing girişimleri
        malicious_urls = [
            "https://huggingface.co.evil.com/model.gguf",
            "https://gpt4all.io.attacker.site/model.bin",
            "https://huggingface.co.malware.com/payload.gguf",
            "https://fake-huggingface.co/model.gguf",
        ]
        
        for url in malicious_urls:
            assert not service._validate_model_url(url), f"Bypass tespit edildi: {url}"
    
    def test_http_downgrade_blocked(self):
        """HTTP downgrade saldırıları engellenmeli"""
        from app.services.ai_service import LocalAIService
        
        service = LocalAIService.__new__(LocalAIService)
        
        # HTTP (güvensiz) URL'ler
        assert not service._validate_model_url("http://huggingface.co/model.gguf")
        assert not service._validate_model_url("http://gpt4all.io/model.bin")
    
    def test_valid_urls_accepted(self):
        """Geçerli URL'ler kabul edilmeli"""
        from app.services.ai_service import LocalAIService
        
        service = LocalAIService.__new__(LocalAIService)
        
        valid_urls = [
            "https://huggingface.co/model.gguf",
            "https://gpt4all.io/models/file.bin",
            "https://ollama.ai/library/model.gguf",
            "https://www.huggingface.co/user/model.gguf",
        ]
        
        for url in valid_urls:
            assert service._validate_model_url(url), f"Geçerli URL reddedildi: {url}"


class TestCircuitBreakerThreadSafety:
    """Circuit Breaker thread safety testleri - Kritik 2"""
    
    @pytest.mark.asyncio
    async def test_has_async_lock(self):
        """asyncio.Lock mevcut olmalı"""
        from app.services.external_service import ExternalService
        
        service = ExternalService()
        assert hasattr(service, '_cb_lock')
        assert isinstance(service._cb_lock, asyncio.Lock)
    
    @pytest.mark.asyncio
    async def test_concurrent_failures_counted_correctly(self):
        """Concurrent hatalar doğru sayılmalı"""
        from app.services.external_service import ExternalService
        
        service = ExternalService()
        
        # 10 concurrent failure
        await asyncio.gather(*[service._record_failure() for _ in range(10)])
        
        # Tüm hatalar sayılmalı
        assert service._cb_failure_count == 10
    
    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Başarı hata sayısını sıfırlamalı"""
        from app.services.external_service import ExternalService
        
        service = ExternalService()
        
        await service._record_failure()
        await service._record_failure()
        assert service._cb_failure_count == 2
        
        await service._record_success()
        assert service._cb_failure_count == 0


class TestImportValidation:
    """Import Service validation testleri - Kritik 3"""
    
    def test_plaka_validation_valid(self):
        """Geçerli plakalar kabul edilmeli"""
        from app.core.services.import_service import ImportService
        
        service = ImportService()
        
        valid_plakas = ["34ABC123", "06DEF45", "35GHI789", "01A1234"]
        for plaka in valid_plakas:
            result = service._validate_plaka(plaka)
            assert result is not None, f"Geçerli plaka reddedildi: {plaka}"
    
    def test_plaka_validation_invalid(self):
        """Geçersiz plakalar reddedilmeli"""
        from app.core.services.import_service import ImportService
        
        service = ImportService()
        
        invalid_plakas = [
            "INVALID",
            "12345",
            "AB",
            "<script>alert(1)</script>",
            "'; DROP TABLE--",
        ]
        
        for plaka in invalid_plakas:
            with pytest.raises(ValueError):
                service._validate_plaka(plaka)
    
    def test_name_validation(self):
        """İsim validation çalışmalı"""
        from app.core.services.import_service import ImportService
        
        service = ImportService()
        
        # Geçerli isimler
        assert service._validate_name("Ahmet Yılmaz") == "Ahmet Yılmaz"
        assert service._validate_name("mehmet öz") == "Mehmet Öz"
        
        # Geçersiz isimler
        with pytest.raises(ValueError):
            service._validate_name("")
        
        with pytest.raises(ValueError):
            service._validate_name("A")  # Çok kısa
    
    def test_location_validation(self):
        """Konum validation çalışmalı"""
        from app.core.services.import_service import ImportService
        
        service = ImportService()
        
        assert service._validate_location("İstanbul") is not None
        assert service._validate_location("Ankara (Merkez)") is not None
        
        with pytest.raises(ValueError):
            service._validate_location("")
    
    def test_numeric_validation(self):
        """Sayısal validation çalışmalı"""
        from app.core.services.import_service import ImportService
        
        service = ImportService()
        
        assert service._validate_numeric(100, "Test", 0, 1000) == 100.0
        assert service._validate_numeric("50.5", "Test") == 50.5
        
        with pytest.raises(ValueError):
            service._validate_numeric("abc", "Test")


class TestCorrelationID:
    """Correlation ID testleri - Kritik 4"""
    
    def test_context_module_exists(self):
        """Context modülü import edilebilmeli"""
        from app.infrastructure.context import (
            get_correlation_id,
            set_correlation_id,
            clear_context
        )
        
        assert callable(get_correlation_id)
        assert callable(set_correlation_id)
        assert callable(clear_context)
    
    def test_correlation_id_set_get(self):
        """Correlation ID set/get çalışmalı"""
        from app.infrastructure.context.request_context import (
            set_correlation_id, get_correlation_id, clear_context
        )
        
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"
        
        clear_context()
    
    def test_middleware_exists(self):
        """Correlation middleware import edilebilmeli"""
        from app.infrastructure.context.correlation_middleware import CorrelationMiddleware
        assert CorrelationMiddleware is not None


class TestAuditDecoratorApplication:
    """Audit decorator uygulama testleri - Kritik 5"""
    
    def test_sefer_service_has_audit_decorators(self):
        """SeferService audit decorator'lara sahip olmalı"""
        from app.core.services.sefer_service import SeferService
        import inspect
        
        source = inspect.getsource(SeferService)
        
        # Audit decorator kullanımları
        assert "@audit_log" in source
        assert 'audit_log("CREATE"' in source or "audit_log('CREATE'" in source
        assert 'audit_log("UPDATE"' in source or "audit_log('UPDATE'" in source
        assert 'audit_log("DELETE"' in source or "audit_log('DELETE'" in source


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Entegrasyon testleri"""
    
    @pytest.mark.asyncio
    async def test_external_service_full_flow(self):
        """External service tam akış testi"""
        from app.services.external_service import ExternalService
        
        service = ExternalService()
        
        # Circuit breaker kapalı başlamalı
        assert service._cb_is_open is False
        
        # 4 hata - hala açık olmamalı
        for _ in range(4):
            await service._record_failure()
        assert service._cb_is_open is False
        
        # 5. hata - açılmalı
        await service._record_failure()
        assert service._cb_is_open is True
        
        # Circuit açıkken istek engellenmeli
        assert await service._check_circuit_breaker() is False
        
        # Başarı sıfırlamalı
        await service._record_success()
        assert service._cb_is_open is False


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCasesV2:
    """Edge case testleri v2"""
    
    def test_empty_plaka(self):
        """Boş plaka hata vermeli"""
        from app.core.services.import_service import ImportService
        
        service = ImportService()
        
        with pytest.raises(ValueError):
            service._validate_plaka("")
        
        with pytest.raises(ValueError):
            service._validate_plaka(None)
    
    def test_unicode_location(self):
        """Unicode lokasyonlar desteklenmeli"""
        from app.core.services.import_service import ImportService
        
        service = ImportService()
        
        result = service._validate_location("İstanbul/Şişli")
        assert "Şişli" in result
    
    def test_url_with_port(self):
        """Port içeren URL'ler işlenmeli"""
        from app.services.ai_service import LocalAIService
        
        service = LocalAIService.__new__(LocalAIService)
        
        # Port ile
        assert service._validate_model_url("https://huggingface.co:443/model.gguf")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
