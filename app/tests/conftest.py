import warnings
# Suppress DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import asyncio
import contextlib
import os
import sys
import uuid
from datetime import date, datetime
from pathlib import Path
from decimal import Decimal
from typing import Optional, Any, Dict, List

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Path setup
APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR.parent))

# Env vars (Will be updated by fixtures)
os.environ["OPENROUTESERVICE_API_KEY"] = "dummy_test_key"
os.environ["OPENROUTE_API_KEY"] = "dummy_test_key"
os.environ["CORS_ORIGINS"] = "http://localhost"

from app.database.models import Base
import app.database.repositories.arac_repo as arac_mod
import app.database.repositories.sefer_repo as sefer_mod
import app.database.repositories.sofor_repo as sofor_mod
import app.database.repositories.yakit_repo as yakit_mod
import app.database.repositories.analiz_repo as analiz_mod
import app.core.container as container_mod

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop

def reset_all_singletons():
    # Reset repo singletons
    arac_mod._arac_repo = None
    sefer_mod._sefer_repo = None
    sofor_mod._sofor_repo = None
    yakit_mod._yakit_repo = None
    analiz_mod._analiz_repo = None
    # Reset container
    container_mod.reset_container()

@pytest.fixture
def temp_db_url(tmp_path):
    # Every test gets a unique file to avoid state leakage
    db_file = tmp_path / f"test_{uuid.uuid4().hex}.sqlite"
    return f"sqlite+aiosqlite:///{db_file.as_posix()}?cache=shared"

@pytest.fixture
async def async_db_engine(temp_db_url):
    engine = create_async_engine(
        temp_db_url,
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Initialize Schema via ORM Models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(async_db_engine, temp_db_url, monkeypatch):
    AsyncTestingSessionLocal = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    session = AsyncTestingSessionLocal()

    # Monkeypatch for components using the global pool
    monkeypatch.setattr("app.database.connection.AsyncSessionLocal", AsyncTestingSessionLocal)
    monkeypatch.setattr("app.database.unit_of_work.AsyncSessionLocal", AsyncTestingSessionLocal)

    # Sync support
    sync_url = temp_db_url.replace("+aiosqlite", "")
    sync_engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    SyncTestingSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
    monkeypatch.setattr("app.database.connection.SyncSessionLocal", SyncTestingSessionLocal)

    reset_all_singletons()
    try:
        yield session
    finally:
        await session.close()
        reset_all_singletons()

# --- Repository Fixtures ---

@pytest.fixture
def arac_repo(db_session):
    from app.database.repositories.arac_repo import AracRepository
    return AracRepository(session=db_session)

@pytest.fixture
def sefer_repo(db_session):
    from app.database.repositories.sefer_repo import SeferRepository
    return SeferRepository(session=db_session)

@pytest.fixture
def yakit_repo(db_session):
    from app.database.repositories.yakit_repo import YakitRepository
    return YakitRepository(session=db_session)

@pytest.fixture
def sofor_repo(db_session):
    from app.database.repositories.sofor_repo import SoforRepository
    return SoforRepository(session=db_session)

# --- Service Fixtures ---

@pytest.fixture
def arac_service(db_session):
    from app.core.services.arac_service import get_arac_service
    return get_arac_service()

@pytest.fixture
def sofor_service(db_session):
    from app.core.services.sofor_service import get_sofor_service
    return get_sofor_service()

@pytest.fixture
def sefer_service(db_session):
    from app.core.services.sefer_service import get_sefer_service
    return get_sefer_service()

@pytest.fixture
def yakit_service(db_session):
    from app.core.services.yakit_service import get_yakit_service
    return get_yakit_service()

@pytest.fixture
def report_service(db_session):
    from app.core.services.report_service import get_report_service
    return get_report_service()

@pytest.fixture
def analiz_service(db_session):
    from app.core.services.analiz_service import get_analiz_service
    return get_analiz_service()

@pytest.fixture
def dashboard_service(db_session):
    from app.core.services.dashboard_service import get_dashboard_service
    return get_dashboard_service()

# --- Sample Data Fixtures ---

@pytest.fixture
def sample_arac_data():
    return {
        "plaka": "34 ABC 123",
        "marka": "Mercedes",
        "model": "Actros",
        "yil": 2022,
        "tank_kapasitesi": 600,
        "hedef_tuketim": 30.5
    }

@pytest.fixture
def sample_sofor_data():
    return {
        "ad_soyad": "Ahmet Yılmaz",
        "telefon": "0532 123 45 67",
        "ehliyet_sinifi": "E",
        "ise_baslama_tarihi": date.today()
    }

@pytest.fixture
def sample_sefer_data():
    return {
        "arac_id": 1,
        "sofor_id": 1,
        "tarih": date.today(),
        "mesafe_km": 450,
        "cikis_yeri": "İstanbul",
        "varis_yeri": "Ankara",
        "baslangic_km": 100000,
        "bitis_km": 100450,
        "baslangic_tarihi": datetime.now(),
        "bitis_tarihi": datetime.now()
    }

@pytest.fixture
def sample_yakit_data():
    return {
        "arac_id": 1,
        "tarih": date.today(),
        "litre": Decimal("100.50"),
        "fiyat_tl": Decimal("40.25"),
        "km_sayac": 100500
    }

@pytest.fixture
async def async_client(db_session):
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(db_session):
    """Admin/Superuser auth headers for tests - Ensures admin exists in DB"""
    from app.core.security import create_access_token, get_password_hash
    from app.database.models import Kullanici
    from sqlalchemy import select
    from datetime import timedelta
    
    # Ensure admin exists
    result = await db_session.execute(select(Kullanici).where(Kullanici.kullanici_adi == "admin"))
    admin = result.scalar_one_or_none()
    
    if not admin:
        admin = Kullanici(
            kullanici_adi="admin",
            sifre_hash=get_password_hash("adminpassword"),
            ad_soyad="Admin User",
            rol="admin",
            aktif=True
        )
        db_session.add(admin)
        await db_session.commit()
    
    token = create_access_token(data={"sub": "admin", "role": "admin"}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def admin_auth_headers(auth_headers):
    return auth_headers

@pytest.fixture
def normal_auth_headers():
    """Normal user auth headers for tests"""
    from app.core.security import create_access_token
    from datetime import timedelta
    token = create_access_token(data={"sub": "testuser", "role": "user"}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}
