"""
Configuration Security Audit Tests
Denetim kriterleri: Secret management, env validation, CORS protection, Alembic safety
"""
import os
import pytest
from pathlib import Path
from pydantic import SecretStr, ValidationError


class TestSecretManagement:
    """A. Secret yönetimi testleri"""
    
    def test_gitignore_exists_at_root(self):
        """Root .gitignore dosyası mevcut olmalı"""
        root = Path(__file__).parent.parent
        gitignore = root / ".gitignore"
        assert gitignore.exists(), "Root .gitignore eksik!"
    
    def test_gitignore_ignores_env_files(self):
        """Gitignore .env dosyalarını ignore etmeli"""
        root = Path(__file__).parent.parent
        gitignore = root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            assert ".env" in content, ".env gitignore'da olmalı"
            assert "*.env" in content, "*.env gitignore'da olmalı"
    
    def test_env_example_no_real_secrets(self):
        """Env example gerçek secret içermemeli"""
        example = Path(__file__).parent.parent / "app" / ".env.example"
        if example.exists():
            content = example.read_text()
            # Gerçek değer içeren pattern'ler (analiz sırasında bulunanlar)
            assert "!23efe25ali!" not in content, "Env example gerçek şifre içeriyor!"
            assert "9e8769c89487c698" not in content, "Env example gerçek secret key içeriyor!"
            assert "eyJvcm" not in content, "Env example gerçek API key içeriyor!"


class TestConfigSafety:
    """B. Config.py güvenlik testleri"""
    
    def test_secret_fields_are_secretstr(self):
        """Kritik alanlar SecretStr tipinde olmalı"""
        from app.config import Settings
        import typing
        hints = typing.get_type_hints(Settings)
        assert hints.get('SECRET_KEY') == SecretStr, "SECRET_KEY SecretStr olmalı"
        assert hints.get('ADMIN_PASSWORD') == SecretStr, "ADMIN_PASSWORD SecretStr olmalı"
    
    def test_environment_validation(self):
        """Environment değeri dev/prod/test olmalı"""
        from app.config import Settings
        
        with pytest.raises(ValidationError):
            Settings(
                SECRET_KEY="test",
                ADMIN_PASSWORD="test",
                DATABASE_URL="sqlite:///test.db",
                OPENROUTESERVICE_API_KEY="test",
                ENVIRONMENT="invalid"
            )

    def test_masked_database_url(self):
        """masked_database_url şifreyi gizlemeli"""
        from app.config import Settings
        s = Settings(
            SECRET_KEY="test",
            ADMIN_PASSWORD="test",
            DATABASE_URL="postgresql://user:secret_pass@localhost:5432/db",
            OPENROUTESERVICE_API_KEY="test"
        )
        assert "secret_pass" not in s.masked_database_url
        assert "***" in s.masked_database_url


class TestCorsProtection:
    """C. CORS wildcard koruması testleri"""
    
    def test_cors_wildcard_blocked_in_prod(self):
        """Prod'da CORS wildcard kabul edilmemeli"""
        from app.config import Settings
        
        # ENVIRONMENT'ı geçici olarak prod yap
        os.environ["ENVIRONMENT"] = "prod"
        try:
            with pytest.raises(ValidationError) as exc_info:
                Settings(
                    SECRET_KEY="test",
                    ADMIN_PASSWORD="test",
                    DATABASE_URL="sqlite:///test.db",
                    OPENROUTESERVICE_API_KEY="test",
                    ENVIRONMENT="prod",
                    CORS_ORIGINS=["*"]
                )
            assert "production" in str(exc_info.value).lower()
        finally:
            os.environ["ENVIRONMENT"] = "dev"


class TestAlembicConfig:
    """D. Alembic.ini güvenlik testleri"""
    
    def test_alembic_no_hardcoded_credentials(self):
        """Alembic.ini hardcoded credential içermemeli"""
        alembic_ini = Path(__file__).parent.parent / "alembic.ini"
        content = alembic_ini.read_text()
        
        # placeholder kontrolü
        assert "driver://user:pass@" not in content, "Alembic.ini hardcoded placeholder içeriyor!"
        
        # sqlalchemy.url kontrolü (boş veya yorum satırı olmalı)
        for line in content.splitlines():
            if line.startswith("sqlalchemy.url"):
                url_val = line.split("=")[1].strip()
                assert url_val == "", f"sqlalchemy.url boş olmalı, bulunan: {url_val}"
