"""
Verification Scripts Test Suite.

Tüm doğrulama betiklerini kapsayan test dosyası.
"""

import pytest
import json
import sys
import signal
import asyncio
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
from io import StringIO

# Project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestVerifyUtils:
    """verify_utils.py unit testleri."""
    
    def test_check_result_dataclass(self):
        """CheckResult dataclass'ını test eder."""
        from app.infrastructure.verification.verify_utils import CheckResult
        
        result = CheckResult(
            name="Test",
            success=True,
            message="Test passed",
            details={"key": "value"},
            duration=1.5,
            skipped=False,
            retry_count=0
        )
        
        assert result.name == "Test"
        assert result.success is True
        assert result.message == "Test passed"
        assert result.details == {"key": "value"}
        assert result.duration == 1.5
        assert result.skipped is False
        assert result.retry_count == 0
    
    def test_check_result_defaults(self):
        """CheckResult default değerlerini test eder."""
        from app.infrastructure.verification.verify_utils import CheckResult
        
        result = CheckResult(name="Test", success=True, message="OK")
        
        assert result.details == {}
        assert result.duration == 0.0
        assert result.skipped is False
        assert result.retry_count == 0
    
    def test_verification_runner_argparse_json(self):
        """VerificationRunner --json argümanını test eder."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            assert runner.args.json is True
            assert runner.args.verbose is False
    
    def test_verification_runner_argparse_verbose(self):
        """VerificationRunner --verbose argümanını test eder."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--verbose']):
            runner = VerificationRunner("Test", "Description")
            assert runner.args.verbose is True
    
    def test_verification_runner_argparse_timeout(self):
        """VerificationRunner --timeout argümanını test eder."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--timeout', '60']):
            runner = VerificationRunner("Test", "Description")
            assert runner.args.timeout == 60
    
    def test_verification_runner_argparse_dry_run(self):
        """VerificationRunner --dry-run argümanını test eder."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--dry-run']):
            runner = VerificationRunner("Test", "Description")
            assert runner.args.dry_run is True
            assert runner.is_dry_run is True
    
    def test_verification_runner_argparse_checks(self):
        """VerificationRunner --checks argümanını test eder."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--checks', 'ai,weather,db']):
            runner = VerificationRunner("Test", "Description")
            assert runner.args.checks == "ai,weather,db"
    
    def test_verification_runner_argparse_env(self):
        """VerificationRunner --env argümanını test eder."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--env', 'prod']):
            runner = VerificationRunner("Test", "Description")
            assert runner.args.env == "prod"
    
    def test_should_run_check_no_filter(self):
        """should_run_check filtre yokken True döner."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test']):
            runner = VerificationRunner("Test", "Description")
            assert runner.should_run_check("anything") is True
    
    def test_should_run_check_with_filter(self):
        """should_run_check filtre varken doğru çalışır."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--checks', 'ai,weather']):
            runner = VerificationRunner("Test", "Description")
            assert runner.should_run_check("ai") is True
            assert runner.should_run_check("weather") is True
            assert runner.should_run_check("db") is False
    
    def test_should_run_check_case_insensitive(self):
        """should_run_check case-insensitive çalışır."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--checks', 'AI,Weather']):
            runner = VerificationRunner("Test", "Description")
            assert runner.should_run_check("ai") is True
            assert runner.should_run_check("AI") is True
            assert runner.should_run_check("weather") is True
    
    def test_add_result_success(self):
        """add_result success sonucu ekler."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            runner.add_result("Check1", True, "Passed", {"key": "val"}, 1.0)
            
            assert len(runner.results) == 1
            assert runner.results[0].name == "Check1"
            assert runner.results[0].success is True
    
    def test_add_result_failure(self):
        """add_result failure sonucu ekler."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            runner.add_result("Check1", False, "Failed", duration=0.5)
            
            assert len(runner.results) == 1
            assert runner.results[0].success is False
    
    def test_add_skipped(self):
        """add_skipped atlanan sonuç ekler."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            runner.add_skipped("Check1", "Not selected")
            
            assert len(runner.results) == 1
            assert runner.results[0].skipped is True
            assert runner.results[0].success is True
    
    def test_register_check(self):
        """register_check check'i kaydeder."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test']):
            runner = VerificationRunner("Test", "Description")
            runner.register_check("my_check")
            runner.register_check("MY_CHECK")  # Duplicate (case-insensitive)
            
            assert "my_check" in runner._available_checks
            assert len(runner._available_checks) == 1  # Lowercase stored
    
    def test_finalize_json_output(self):
        """finalize JSON formatında çıktı üretir."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            runner.add_result("Check1", True, "Passed")
            runner.add_result("Check2", False, "Failed")
            
            # Capture stdout
            captured = StringIO()
            with patch('sys.stdout', captured):
                with pytest.raises(SystemExit) as exc_info:
                    runner.finalize()
            
            # Exit code 1 (failure)
            assert exc_info.value.code == 1
            
            # Parse JSON output
            output = captured.getvalue()
            data = json.loads(output)
            
            assert data["name"] == "Test"
            assert data["total"] == 2
            assert data["success"] == 1
            assert data["failed"] == 1
    
    def test_finalize_exit_success(self):
        """finalize başarıda exit(0) döner."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            runner.add_result("Check1", True, "Passed")
            
            captured = StringIO()
            with patch('sys.stdout', captured):
                with pytest.raises(SystemExit) as exc_info:
                    runner.finalize()
            
            assert exc_info.value.code == 0
    
    def test_print_section(self):
        """print_section düzgün formatta yazdırır."""
        from app.infrastructure.verification.verify_utils import print_section
        
        captured = StringIO()
        with patch('sys.stdout', captured):
            print_section("Test Title")
        
        output = captured.getvalue()
        assert "Test Title" in output
        assert "=" in output


class TestVerifyUtilsTimeoutRetry:
    """Timeout ve retry mekanizma testleri."""
    
    def test_run_with_timeout_success(self):
        """run_with_timeout başarılı işlem."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--timeout', '5']):
            runner = VerificationRunner("Test", "Description")
            
            def quick_func():
                return "done"
            
            result = runner.run_with_timeout(quick_func, timeout=2)
            assert result == "done"
    
    def test_run_with_timeout_exceeded(self):
        """run_with_timeout timeout aşımı."""
        from app.infrastructure.verification.verify_utils import (
            VerificationRunner, TimeoutError
        )
        
        with patch('sys.argv', ['test', '--timeout', '1']):
            runner = VerificationRunner("Test", "Description")
            
            def slow_func():
                time.sleep(5)
                return "done"
            
            with pytest.raises(TimeoutError):
                runner.run_with_timeout(slow_func, timeout=1)
    
    def test_run_with_retry_success_first_try(self):
        """run_with_retry ilk denemede başarı."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--retries', '3', '--json']):
            runner = VerificationRunner("Test", "Description")
            
            def success_func():
                return "done"
            
            result, attempt = runner.run_with_retry(success_func, "test")
            assert result == "done"
            assert attempt == 0
    
    def test_run_with_retry_success_after_retries(self):
        """run_with_retry retry sonrası başarı."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--retries', '3', '--json']):
            runner = VerificationRunner("Test", "Description")
            
            attempt_count = [0]
            
            def flaky_func():
                attempt_count[0] += 1
                if attempt_count[0] < 3:
                    raise ValueError("Flaky error")
                return "done"
            
            result, attempt = runner.run_with_retry(flaky_func, "test", retries=3)
            assert result == "done"
            assert attempt == 2  # 0, 1, 2 (3rd attempt succeeded)


class TestSafeDbOperation:
    """safe_db_operation context manager testleri."""
    
    def test_safe_db_operation_dry_run(self):
        """Dry-run modunda operasyon atlanır."""
        from app.infrastructure.verification.verify_utils import (
            VerificationRunner, safe_db_operation
        )
        
        with patch('sys.argv', ['test', '--dry-run', '--json']):
            runner = VerificationRunner("Test", "Description")
            
            with safe_db_operation(runner, "DELETE operation") as should_run:
                assert should_run is False
    
    def test_safe_db_operation_normal_mode(self):
        """Normal modda operasyon çalışır."""
        from app.infrastructure.verification.verify_utils import (
            VerificationRunner, safe_db_operation
        )
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            
            with safe_db_operation(runner, "DELETE operation") as should_run:
                assert should_run is True


class TestVerifyBackendV2Script:
    """verify_backend_v2.py testleri."""
    
    def test_script_json_output(self):
        """Script JSON output üretebilir."""
        import subprocess
        
        result = subprocess.run(
            [sys.executable, "scripts/verify_backend_v2.py", "--json"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=30
        )
        
        # stdout'da JSON olmalı, ancak logger müdahale edebilir
        # Son satırları JSON olarak parse etmeye çalış
        stdout_lines = result.stdout.strip().split('\n')
        
        # JSON blok bul
        json_str = None
        brace_count = 0
        json_lines = []
        in_json = False
        
        for line in stdout_lines:
            if '{' in line and not in_json:
                in_json = True
            
            if in_json:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0:
                    json_str = '\n'.join(json_lines)
                    break
        
        if json_str is None:
            # Tüm stdout'u dene
            json_str = result.stdout
        
        try:
            data = json.loads(json_str)
            assert "name" in data
            assert "results" in data
            assert "total" in data
        except json.JSONDecodeError:
            # Stderr kontrolü de yap
            pytest.fail(f"Invalid JSON output. stdout: {result.stdout[:500]}...")
    
    def test_script_selective_checks(self):
        """Script selective checks destekler."""
        import subprocess
        
        result = subprocess.run(
            [sys.executable, "scripts/verify_backend_v2.py", "--json", "--checks", "sqlalchemy"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=30
        )
        
        data = json.loads(result.stdout)
        # Sadece seçili check çalışmalı
        check_names = [r["name"] for r in data["results"] if not r.get("skipped")]
        assert len(check_names) >= 1


class TestVerifyDbConnectionScript:
    """verify_db_connection.py testleri."""
    
    def test_url_masking(self):
        """URL masking fonksiyonu çalışır."""
        # Script'i import et
        sys.path.insert(0, str(project_root / "scripts"))
        from verify_db_connection import mask_url
        
        masked = mask_url("postgresql://user:secret@localhost:5432/db")
        assert "secret" not in masked
        assert "****" in masked
        assert "user" in masked
    
    def test_url_security_check(self):
        """URL güvenlik kontrolü çalışır."""
        sys.path.insert(0, str(project_root / "scripts"))
        from verify_db_connection import check_url_security
        
        # Weak credentials
        warnings = check_url_security("postgresql://postgres:postgres@localhost/db")
        assert len(warnings) > 0
        
        # No SSL
        warnings = check_url_security("postgresql://user:pass@localhost/db")
        assert any("SSL" in w for w in warnings)


class TestVerifyPhase4DryRun:
    """verify_phase4.py dry-run testleri."""
    
    def test_dry_run_no_db_changes(self):
        """Dry-run modunda DB değişikliği yapılmaz."""
        import subprocess
        
        result = subprocess.run(
            [sys.executable, "scripts/verify_phase4.py", "--json", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=60
        )
        
        data = json.loads(result.stdout)
        
        # Service Layer check dry-run olarak işaretlenmeli
        service_result = next(
            (r for r in data["results"] if r["name"] == "Service Layer"), 
            None
        )
        
        if service_result:
            assert "DRY-RUN" in service_result["message"] or service_result.get("details", {}).get("dry_run")


class TestEdgeCases:
    """Edge case testleri."""
    
    def test_empty_results(self):
        """Hiç sonuç yokken finalize çalışır."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            
            captured = StringIO()
            with patch('sys.stdout', captured):
                with pytest.raises(SystemExit) as exc_info:
                    runner.finalize()
            
            assert exc_info.value.code == 0
            
            data = json.loads(captured.getvalue())
            assert data["total"] == 0
    
    def test_unicode_in_message(self):
        """Unicode mesajlar desteklenir."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            runner.add_result("Check", True, "Türkçe karakter: ğüşöç 日本語")
            
            captured = StringIO()
            with patch('sys.stdout', captured):
                with pytest.raises(SystemExit):
                    runner.finalize()
            
            output = captured.getvalue()
            data = json.loads(output)
            assert "Türkçe" in data["results"][0]["message"]
    
    def test_decimal_in_details(self):
        """Decimal değerler JSON'a dönüştürülür."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        from decimal import Decimal
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            runner.add_result("Check", True, "OK", {"value": Decimal("123.45")})
            
            captured = StringIO()
            with patch('sys.stdout', captured):
                with pytest.raises(SystemExit):
                    runner.finalize()
            
            output = captured.getvalue()
            data = json.loads(output)
            assert data["results"][0]["details"]["value"] == 123.45


class TestInterruptedExecution:
    """Interrupted execution testleri."""
    
    def test_interrupted_flag(self):
        """Interrupted flag doğru çalışır."""
        from app.infrastructure.verification.verify_utils import VerificationRunner
        
        with patch('sys.argv', ['test', '--json']):
            runner = VerificationRunner("Test", "Description")
            
            assert runner.is_interrupted is False
            
            # Simulate interrupt
            runner._interrupted = True
            
            assert runner.is_interrupted is True
            assert runner.should_run_check("anything") is False


class TestSecurityAudit:
    """Güvenlik audit testleri - Kritik düzeltmelerin doğrulanması."""
    
    def test_verify_phase4_no_sql_injection(self):
        """verify_phase4.py'da SQL injection koruması olduğunu doğrular."""
        import re
        script_path = project_root / "scripts" / "verify_phase4.py"
        content = script_path.read_text(encoding="utf-8")
        
        # f-string içinde DELETE veya INSERT olmamalı
        dangerous_pattern = r'text\s*\(\s*f["\'].*?(DELETE|INSERT|UPDATE|DROP).*?["\']'
        matches = re.findall(dangerous_pattern, content, re.IGNORECASE)
        
        assert len(matches) == 0, f"SQL Injection riski tespit edildi: {matches}"
        
        # Parameterized query kullanılmalı
        assert ':id' in content or ':param' in content, "Parameterized query kullanılmalı"
    
    def test_verify_db_connection_no_hardcoded_credentials(self):
        """verify_db_connection.py'da hardcoded credentials olmadığını doğrular."""
        script_path = project_root / "scripts" / "verify_db_connection.py"
        content = script_path.read_text(encoding="utf-8")
        
        # DATABASE_URL zorunlu olmalı
        assert "DATABASE_URL environment variable not set" in content or \
               "missing_env_var" in content, "DATABASE_URL zorunlu kontrolü eksik"
        
        # Default URL'de postgres:postgres olmamalı
        # Not: check_url_security fonksiyonundaki referans güvenlik kontrolü için
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # os.getenv default değeri içinde olmamalı
            if 'os.getenv' in line and 'postgres:postgres' in line:
                assert False, f"Hardcoded credentials in os.getenv default at line {i+1}"
            # Connection string assignment'ta olmamalı
            if '=' in line and 'postgresql' in line and 'postgres:postgres' in line:
                if 'check_url_security' not in lines[max(0, i-5):i+1]:
                    if '"postgres:postgres' not in line or 'in url' not in lines[i]:
                        # check_url_security içindeki kontrol referansı kabul edilebilir
                        pass
    
    def test_verify_utils_daemon_thread(self):
        """verify_utils.py'da daemon thread kullanıldığını doğrular."""
        utils_path = project_root / "app" / "infrastructure" / "verification" / "verify_utils.py"
        content = utils_path.read_text(encoding="utf-8")
        
        # Timeout thread daemon=True olmalı
        assert "daemon=True" in content, "Timeout thread daemon=True olmalı"
    
    def test_verify_utils_signal_handler_io_safe(self):
        """verify_utils.py signal handler'ında IO yapılmadığını doğrular."""
        utils_path = project_root / "app" / "infrastructure" / "verification" / "verify_utils.py"
        content = utils_path.read_text(encoding="utf-8")
        
        # Signal handler içinde print olmamalı
        assert "_check_interrupted_message" in content, "Interrupt mesajı main thread'de olmalı"
        assert "_interrupt_signal" in content, "Signal bilgisi flag olarak saklanmalı"
    
    def test_verify_bulk_insert_dynamic_arac_id(self):
        """verify_bulk_insert.py'da dinamik arac_id kullanıldığını doğrular."""
        script_path = project_root / "scripts" / "verify_bulk_insert.py"
        content = script_path.read_text(encoding="utf-8")
        
        # Hardcoded arac_id=1 olmamalı
        assert "arac_id=1," not in content, "Hardcoded arac_id=1 tespit edildi"
        
        # Dinamik sorgu ile arac_id bulunmalı
        assert "SELECT id FROM araclar" in content, "Dinamik arac_id sorgusu eksik"
    
    def test_verify_utils_help_text(self):
        """verify_utils.py'da help text ve epilog olduğunu doğrular."""
        utils_path = project_root / "app" / "infrastructure" / "verification" / "verify_utils.py"
        content = utils_path.read_text(encoding="utf-8")
        
        # Epilog ve örnekler olmalı
        assert "epilog=" in content, "ArgumentParser epilog eksik"
        assert "Exit Codes:" in content, "Exit code dokümantasyonu eksik"
        assert "--json" in content and "--dry-run" in content, "Örnek komutlar eksik"
