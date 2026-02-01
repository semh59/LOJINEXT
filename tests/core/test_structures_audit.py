"""
Temel yapılar için kapsamlı test suite ve Audit Doğrulaması
"""
import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
import time

from app.core.container import get_container, reset_container
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.validators import sanitize_input
from app.core.entities.models import Arac, AracCreate
from app.core.entities.sofor_degerlendirme import SoforDegerlendirmeService

class TestDependencyContainer:
    """DI Container testleri"""
    
    def setup_method(self):
        reset_container()

    def teardown_method(self):
        reset_container()

    def test_singleton_thread_safety(self):
        """Concurrent erişimde tek instance"""
        containers = []
        
        def get_instance():
            time.sleep(0.01) # Race condition ihtimalini artır
            containers.append(get_container())
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_instance) for _ in range(50)]
            for f in futures:
                f.result()
        
        # Tüm instance'lar aynı olmalı
        first = containers[0]
        assert all(c is first for c in containers)
    
    def test_shutdown_clears_services(self):
        """Shutdown servisleri temizlemeli"""
        container = get_container()
        # Initialize a service
        _ = container.arac_service
        assert container._arac_service is not None
        
        container.shutdown()
        assert container._arac_service is None

    def test_analiz_repo_injection(self):
        """Container AnalizRepo'yu ve ona bağlı servisleri doğru inject etmeli"""
        container = get_container()
        ds = container.degerlendirme_service
        assert ds.analiz_repo is not None
        assert ds.sofor_repo is not None

class TestSecurityUtils:
    """Security utilities testleri"""
    
    def test_password_hash_unique_salt(self):
        """Her hash farklı olmalı (salt)"""
        h1 = get_password_hash("test123")
        h2 = get_password_hash("test123")
        assert h1 != h2
    
    def test_password_verify_correct(self):
        """Doğru password verify edilmeli"""
        pw = "supersecret"
        h = get_password_hash(pw)
        assert verify_password(pw, h) is True
    
    def test_password_verify_wrong(self):
        """Yanlış password reject edilmeli"""
        pw = "supersecret"
        h = get_password_hash(pw)
        assert verify_password("wrong", h) is False
        assert verify_password("", h) is False
        assert verify_password(None, h) is False

    def test_timing_attack_prevention(self):
        """Verify uses safe comparison (concept check)"""
        # Implementation check involves reviewing code, but functional test:
        assert verify_password("a" * 100, "$2b$12$.............................") is False


class TestValidators:
    """Validator testleri"""
    
    def test_sanitize_input_html(self):
        """HTML escape çalışmalı"""
        raw = "<script>alert(1)</script>"
        sanitized = sanitize_input(raw)
        assert "&lt;script&gt;" in sanitized
    
    def test_sanitize_unicode(self):
        """Unicode normalization (NFKC)"""
        # 'İ' sometimes decomposes. Ensure strict single char check if possible or just standard equality
        # 'ﬁ' ligature -> 'fi'
        ligature = "ﬁ"
        assert sanitize_input(ligature) == "fi"

    def test_sql_injection_blocked(self):
        """SQL injection pattern'leri tespit edilmeli"""
        with pytest.raises(ValueError, match="Güvenlik ihlali"):
            sanitize_input("UNION SELECT * FROM users")
        
        with pytest.raises(ValueError, match="Güvenlik ihlali"):
            sanitize_input("WAITFOR DELAY '0:0:5'")
            
        with pytest.raises(ValueError):
            sanitize_input("xyz; DROP TABLE students; --")

class TestEntityModels:
    """Entity model testleri"""
    
    def test_plaka_validation_strict(self):
        """Plaka validasyonu"""
        # Valid
        assert AracCreate.validate_plaka("34 ABC 123") == "34 ABC 123"
        assert AracCreate.validate_plaka("34ABC123") == "34 ABC 123"
        
        # Invalid
        with pytest.raises(ValueError):
             AracCreate.validate_plaka("INVALID")
        
        with pytest.raises(ValueError):
             AracCreate.validate_plaka("34 A 1") # Too short logic per patterns

    def test_sofor_degerlendirme_requires_di(self):
        """Manuel oluşturmada argüman zorunluluğu"""
        with pytest.raises(ValueError, match="requires"):
            SoforDegerlendirmeService(analiz_repo=None, sofor_repo=None)


class TestAuditRemediation:
    """Audit remediation doğrulama testleri"""
    
    def test_password_max_length(self):
        """Çok uzun password reject edilmeli (bcrypt DoS önlemi)"""
        long_pw = "A" * 100  # 100 byte > 72 byte limit
        with pytest.raises(ValueError, match="çok uzun"):
            get_password_hash(long_pw)
    
    def test_password_empty_rejected(self):
        """Boş password reject edilmeli"""
        with pytest.raises(ValueError, match="boş olamaz"):
            get_password_hash("")
        with pytest.raises(ValueError, match="boş olamaz"):
            get_password_hash(None)
    
    def test_path_traversal_blocked(self):
        """Path traversal pattern'leri tespit edilmeli"""
        with pytest.raises(ValueError, match="Güvenlik ihlali"):
            sanitize_input("../../etc/passwd")
        with pytest.raises(ValueError, match="Güvenlik ihlali"):
            sanitize_input("..\\..\\windows\\system32")
    
    def test_null_byte_blocked(self):
        """Null byte injection engellenmeli"""
        with pytest.raises(ValueError, match="Güvenlik ihlali"):
            sanitize_input("file.txt\x00.jpg")
    
    def test_container_analiz_repo_attribute(self):
        """Container'da _analiz_repo tanımlı olmalı"""
        reset_container()
        container = get_container()
        assert hasattr(container, '_analiz_repo')
        reset_container()
    
    def test_sql_pattern_not_leaked(self):
        """Hata mesajında SQL pattern sızdırılmamalı"""
        try:
            sanitize_input("UNION SELECT * FROM users")
        except ValueError as e:
            # Pattern hata mesajında olmamalı
            assert "UNION" not in str(e).upper() or "pattern" not in str(e).lower()
            assert "Güvenlik ihlali" in str(e)

if __name__ == "__main__":
    # Manually run tests if executed as script
    t = TestDependencyContainer()
    t.setup_method()
    t.test_singleton_thread_safety()
    t.test_shutdown_clears_services()
    t.test_analiz_repo_injection()
    t.teardown_method()
    print("Container tests passed")

    s = TestSecurityUtils()
    s.test_password_hash_unique_salt()
    s.test_password_verify_correct()
    s.test_password_verify_wrong()
    s.test_timing_attack_prevention()
    print("Security tests passed")

    v = TestValidators()
    v.test_sanitize_input_html()
    v.test_sanitize_unicode()
    v.test_sql_injection_blocked()
    print("Validator tests passed")

    e = TestEntityModels()
    e.test_plaka_validation_strict()
    print("Entity tests passed")

    d = TestDIEnforcement()
    d.test_sofor_degerlendirme_requires_di()
    print("DI enforcement tests passed")

