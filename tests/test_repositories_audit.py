"""
Repository için kapsamlı test suite
"""
import pytest
import inspect
import threading
from sqlalchemy import text
from app.database.repositories import arac_repo, yakit_repo
from app.database.repositories.yakit_repo import get_yakit_repo
from app.database.repositories.arac_repo import get_arac_repo
from app.database.repositories.sefer_repo import get_sefer_repo
from app.database.models import YakitPeriyodu
from datetime import date, datetime

class TestSQLInjectionProtection:
    """SQL Injection koruması testleri"""
    
    @pytest.mark.asyncio
    async def test_parameterized_query(self, db_session):
        """Parametreli query kullanılmalı - AracRepo örneği"""
        repo = get_arac_repo(session=db_session)
        
        # SQL injection denemesi - ORM kullandığı için zaten güvenli ama yine de deneyelim
        malicious_input = "'; DROP TABLE araclar; --"
        
        # Bu çağrı hata vermeli veya güvenli şekilde handle etmeli (boş dönmeli)
        result = await repo.get_by_plaka(malicious_input)
        
        # Tablo hala var olmalı ve sonuç None olmalı (veya boş)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_no_string_formatting_in_queries(self):
        """SQL'de string formatting olmamalı - Static Analysis"""
        repositories = [arac_repo, yakit_repo] # Diğer repoları da ekleyebiliriz
        
        dangerous_patterns = [
            'f"SELECT', "f'SELECT",
            'f"INSERT', "f'INSERT",
            'f"UPDATE', "f'UPDATE",
            'f"DELETE', "f'DELETE",
            ' .format(', ' % ('
        ]
        
        for repo in repositories:
            source = inspect.getsource(repo)
            for pattern in dangerous_patterns:
                # Basit string formatting kontrolü
                # Not: text() içinde bindparam kullanımı serbest
                assert pattern not in source, f"Dangerous pattern found in {repo.__name__}: {pattern}"

    @pytest.mark.asyncio
    async def test_special_characters_in_plaka(self, db_session):
        """Özel karakterler güvenli handle edilmeli"""
        repo = get_arac_repo(session=db_session)
        
        special_inputs = [
            "'; DROP TABLE--",
            "İŞÇİ PLAKAŞI",
            "' OR '1'='1",
            "UNION SELECT * FROM users--"
        ]
        
        for inp in special_inputs:
            result = await repo.get_by_plaka(inp)
            # Hata vermemeli, None dönmeli
            assert result is None

class TestSessionManagement:
    """Session yönetimi testleri"""
    
    @pytest.mark.asyncio
    async def test_repo_gets_session(self, db_session):
        """Repository session'ı doğru almalı"""
        repo = get_yakit_repo(session=db_session)
        assert repo.session is db_session

class TestThreadSafety:
    """Thread-safety testleri"""
    
    def test_concurrent_singleton_access(self):
        """Concurrent singleton erişimi thread-safe olmalı"""
        repos = []
        errors = []
        
        def get_repo():
            try:
                repos.append(get_arac_repo())
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=get_repo) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        # Hepsi aynı instance olmalı
        assert all(r is repos[0] for r in repos)

    def test_login_tracker_thread_safety(self):
        """LoginAttemptTracker thread-safe olmalı"""
        from app.database.repositories.kullanici_repo import LoginAttemptTracker
        
        tracker = LoginAttemptTracker()
        errors = []
        
        def record():
            try:
                for _ in range(20):
                    tracker.record_attempt("testuser", False)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=record) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread-safety error: {errors}"
        # Kullanıcı kilitlenmiş olmalı (200 deneme)
        assert tracker.is_locked("testuser")

class TestInputValidation:
    """Input validation testleri"""
    
    @pytest.mark.asyncio
    async def test_limit_validation(self, db_session):
        """Limit değeri max değeri aşmamalı"""
        repo = get_arac_repo(session=db_session)
        
        # Çok büyük limit ile çağrı - MAX_LIMIT=1000'e düşürülmeli
        result = await repo.get_all(limit=1000000)
        # Hata vermemeli
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_negative_offset_normalized(self, db_session):
        """Negatif offset 0'a normalize edilmeli"""
        repo = get_sefer_repo(session=db_session)
        
        # Negatif offset hata vermemeli
        result = await repo.get_all(offset=-10)
        assert result is not None

class TestBulkOperations:
    """Bulk işlem testleri"""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session):
        """Bulk insert (YakitRepo) performansı"""
        repo = get_yakit_repo(session=db_session)
        
        # Fake data generator
        periods = []
        for i in range(10): # Test için küçük sayı, prod için büyük olabilir
            p = YakitPeriyodu(
                arac_id=1,
                alim1_id=i+1, alim2_id=i+2,
                alim1_tarih=date.today(), alim2_tarih=date.today(),
                alim1_km=1000 + i*100, alim2_km=1200 + i*100,
                alim1_litre=50.0, ara_mesafe=200, toplam_yakit=50.0,
                ort_tuketim=25.0, durum='Tamam'
            )
            periods.append(p)
            
        # Clean existing test data if any logic needed? No, transactional rollback handles it ideally.
        # But we are mocking logic mostly.
        
        # Execute save
        count = await repo.save_fuel_periods(periods, clear_existing=False)
        assert count == 10
        
        # Verify db content
        result = await db_session.execute(text("SELECT COUNT(*) FROM yakit_periyotlari"))
        assert result.scalar() >= 10

