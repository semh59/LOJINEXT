"""
Database Connectivity Verification Script.

Sync ve Async veritabanı bağlantılarını doğrular.
SSL desteği ve connection timeout kontrolü dahil.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from app.infrastructure.verification.verify_utils import VerificationRunner, print_section

load_dotenv()


def mask_url(url: str) -> str:
    """Veritabanı URL'sindeki credentials'ı maskeler."""
    try:
        from sqlalchemy.engine.url import make_url
        obj = make_url(url)
        masked_pass = "****" if obj.password else ""
        return f"{obj.drivername}://{obj.username}:{masked_pass}@{obj.host}:{obj.port}/{obj.database}"
    except Exception:
        return "[URL Masking Failed - Format Geçersiz]"


def check_url_security(url: str) -> list:
    """URL güvenlik kontrolü yapar."""
    warnings = []
    
    # Hardcoded credential kontrolü
    if "postgres:postgres" in url or "password" in url.lower():
        warnings.append("⚠️ Hardcoded/weak credentials tespit edildi")
    
    # SSL kontrolü
    if "sslmode" not in url and "?ssl" not in url:
        warnings.append("⚠️ SSL parametresi belirtilmemiş (prod için önerilir)")
    
    return warnings


def test_sync(runner: VerificationRunner, url: str):
    """Senkron bağlantı testi."""
    if not runner.should_run_check("sync"):
        runner.add_skipped("Sync Connection", "Not selected")
        return
        
    if not runner.args.json:
        print_section("Testing Sync Connection")
    
    start_time = time.time()
    try:
        # Timeout ile engine oluştur
        engine = create_engine(
            url, 
            connect_args={"connect_timeout": 10},
            pool_pre_ping=True
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            runner.add_result(
                "Sync Connection", 
                True, 
                f"Success! Result: {result}",
                {"driver": engine.driver, "dialect": engine.dialect.name},
                duration=time.time() - start_time
            )
    except Exception as e:
        runner.add_result(
            "Sync Connection", 
            False, 
            f"FAILED: {str(e)}",
            duration=time.time() - start_time
        )


async def test_async(runner: VerificationRunner, url: str):
    """Asenkron bağlantı testi."""
    if not runner.should_run_check("async"):
        runner.add_skipped("Async Connection", "Not selected")
        return
        
    if not runner.args.json:
        print_section("Testing Async Connection")
    
    start_time = time.time()
    try:
        engine = create_async_engine(
            url,
            pool_pre_ping=True,
            connect_args={"timeout": 10}
        )
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            runner.add_result(
                "Async Connection", 
                True, 
                f"Success! Result: {val}",
                {"driver": "asyncpg"},
                duration=time.time() - start_time
            )
    except Exception as e:
        runner.add_result(
            "Async Connection", 
            False, 
            f"FAILED: {str(e)}",
            duration=time.time() - start_time
        )


def test_url_security(runner: VerificationRunner, db_url: str):
    """URL güvenlik kontrolü."""
    if not runner.should_run_check("security"):
        runner.add_skipped("URL Security", "Not selected")
        return
        
    start_time = time.time()
    warnings = check_url_security(db_url)
    
    if warnings:
        runner.add_result(
            "URL Security",
            False,
            f"{len(warnings)} güvenlik uyarısı tespit edildi",
            {"warnings": warnings},
            duration=time.time() - start_time
        )
    else:
        runner.add_result(
            "URL Security",
            True,
            "URL güvenlik kontrolü başarılı",
            duration=time.time() - start_time
        )


async def main():
    runner = VerificationRunner(
        "Database Connectivity", 
        "Validates Sync and Async database access with security checks"
    )
    
    # Check registration
    runner.register_check("sync")
    runner.register_check("async")
    runner.register_check("security")
    
    # DATABASE_URL zorunlu - hardcoded credentials güvenlik riski
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        runner.add_result(
            "Database URL", 
            False, 
            "DATABASE_URL environment variable not set. Example: postgresql+asyncpg://user:pass@host:5432/db",
            {"error": "missing_env_var"}
        )
        runner.finalize()
        return
    
    sync_url = db_url.replace("+asyncpg", "+psycopg2") if "+asyncpg" in db_url else db_url
    
    if runner.args.verbose and not runner.args.json:
        print(f"📌 Async URL: {mask_url(db_url)}")
        print(f"📌 Sync URL: {mask_url(sync_url)}")
    
    # URL güvenlik kontrolü önce
    test_url_security(runner, db_url)
    
    if runner.is_interrupted:
        runner.finalize()
        return
    
    test_sync(runner, sync_url)
    
    if runner.is_interrupted:
        runner.finalize()
        return
        
    await test_async(runner, db_url)
    
    runner.finalize()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
