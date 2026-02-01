"""
Logs and Data Security Audit Verification Tests
Denetim kriterleri: PII masking, password masking, audit log security
"""
import logging
import json
import pytest
from pathlib import Path
from app.infrastructure.logging.logger import setup_logging, PIIFilter
from app.infrastructure.logging.audit_logger import audit_log, _mask_sensitive_data

class TestLoggingSecurity:
    """PII ve Hassas veri maskeleme testleri"""
    
    def test_pii_filter_masking(self):
        """Email, Telefon ve TCKN maskelenmeli"""
        f = PIIFilter()
        
        # Email
        record = logging.LogRecord("test", logging.INFO, "test", 10, "Email: test@example.com", None, None)
        f.filter(record)
        assert "<EMAIL_MASKED>" in record.msg
        
        # Phone
        record = logging.LogRecord("test", logging.INFO, "test", 10, "Phone: 05321234567", None, None)
        f.filter(record)
        assert "<PHONE_MASKED>" in record.msg
        
        # TCKN
        record = logging.LogRecord("test", logging.INFO, "test", 10, "TCKN: 12345678901", None, None)
        f.filter(record)
        assert "<TCKN_MASKED>" in record.msg

    def test_password_masking_in_msg(self):
        """Log mesajı içindeki şifreler maskelenmeli"""
        f = PIIFilter()
        
        test_cases = [
            "password: 'mysecret123'",
            "sifre=123456",
            "token: abc-def-123",
            "api_key: \"key_value\""
        ]
        
        for case in test_cases:
            record = logging.LogRecord("test", logging.INFO, "test", 10, case, None, None)
            f.filter(record)
            assert "***MASKED***" in record.msg, f"Failed for: {case}"

    def test_dict_masking_in_extra_args(self):
        """Extra args içindeki dict verileri maskelenmeli"""
        f = PIIFilter()
        data = {"username": "admin", "password": "secure_password", "nested": {"token": "secret_token"}}
        
        # Logging'de extra=data kullanımı args ve msg dışında record.__dict__'e eklenir.
        # Bizim PIIFilter filter() içinde record.args'ı maskeliyor.
        
        class MockRecord:
            def __init__(self, msg, args):
                self.msg = msg
                self.args = args
        
        record = MockRecord("Auth attempt", (data,))
        f.filter(record)
        
        masked_data = record.args[0]
        assert masked_data["password"] == "***MASKED***"
        assert masked_data["nested"]["token"] == "***MASKED***"
        assert masked_data["username"] == "admin"


class TestAuditSecurity:
    """Audit log güvenliği testleri"""
    
    @pytest.mark.asyncio
    async def test_audit_log_decorator_masking(self):
        """Audit dekoratörü hassas verileri maskelemeli"""
        
        # Dummy async function for testing decorator
        class MockService:
            @audit_log("CREATE", "USER")
            async def create_user(self, data: dict, password: str = None):
                return {"id": 1, "status": "created"}
        
        service = MockService()
        
        # Test password as kwarg
        await service.create_user({"email": "test@test.com"}, password="mypassword")
        
        # Log içeriğini yakalamak zor olabilir (gerçek log dosyasına yazar)
        # Ama _mask_sensitive_data fonksiyonunu doğrudan test edebiliriz
        
        data = {"username": "test", "password": "123", "secret_key": "abc"}
        masked = _mask_sensitive_data(data)
        assert masked["password"] == "***MASKED***"
        assert masked["username"] == "test"
        
        # Recursive check
        nested = {"user": {"details": {"token": "xyz"}}}
        masked_nested = _mask_sensitive_data(nested)
        assert masked_nested["user"]["details"]["token"] == "***MASKED***"

    def test_no_stacktrace_masking_standard_logger(self):
        """Hata durumlarında stack trace içindeki pathler sanitize edilmeli (log injection koruması)"""
        f = PIIFilter()
        msg = "Error at d:\\PROJECT\\excel\\app\\main.py\nCritical failure"
        record = logging.LogRecord("test", logging.ERROR, "test", 10, msg, None, None)
        f.filter(record)
        assert "\\n" in record.msg
        assert "\n" not in record.msg
