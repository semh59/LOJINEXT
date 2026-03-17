import asyncio
import os
import sys
import warnings
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

# Suppress DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Path setup
APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR.parent))

# Env vars (Will be updated by fixtures)
os.environ["OPENROUTESERVICE_API_KEY"] = "dummy_test_key"
os.environ["OPENROUTE_API_KEY"] = "dummy_test_key"
os.environ["CORS_ORIGINS"] = "http://localhost"
os.environ["MAPBOX_API_KEY"] = ""

import app.core.container as container_mod  # noqa: E402
import app.database.repositories.analiz_repo as analiz_mod  # noqa: E402
import app.database.repositories.arac_repo as arac_mod  # noqa: E402
import app.database.repositories.sefer_repo as sefer_mod  # noqa: E402
import app.database.repositories.sofor_repo as sofor_mod  # noqa: E402
import app.database.repositories.yakit_repo as yakit_mod  # noqa: E402
from app.database.models import Base  # noqa: E402


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
def temp_db_url():
    # TEST_DATABASE_URL ortam değişkeninden oku veya varsayılanı kullan
    url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:!23efe25ali!@localhost:5432/lojinext_test",
    )
    return url


@pytest.fixture
async def async_db_engine(temp_db_url):
    engine = create_async_engine(temp_db_url, echo=False)

    # Initialize Schema via ORM Models
    async with engine.begin() as conn:
        # Explicitly drop removed tables to avoid FK issues during drop_all
        await conn.execute(text("DROP TABLE IF EXISTS guzergahlar CASCADE"))
        # Some legacy tables are outside SQLAlchemy metadata and can block drop_all.
        await conn.execute(text("DROP TABLE IF EXISTS alerts CASCADE"))
        # Materialized view can depend on seferler and block drop_all between test runs.
        await conn.execute(
            text("DROP MATERIALIZED VIEW IF EXISTS sefer_istatistik_mv CASCADE")
        )
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Test parity: stats endpoint expects materialized view in PostgreSQL.
        await conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS sefer_istatistik_mv"))
        await conn.execute(
            text(
                """
                CREATE MATERIALIZED VIEW sefer_istatistik_mv AS
                SELECT
                    durum,
                    COUNT(id) AS toplam_sefer,
                    COALESCE(SUM(mesafe_km), 0) AS toplam_km,
                    COALESCE(SUM(otoban_mesafe_km), 0) AS highway_km,
                    COALESCE(SUM(ascent_m), 0) AS total_ascent,
                    COALESCE(SUM(net_kg / 1000.0), 0) AS total_weight,
                    MAX(created_at) AS last_updated
                FROM seferler
                WHERE is_real = TRUE AND is_deleted = FALSE
                GROUP BY durum
                """
            )
        )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX idx_sefer_istatistik_mv_durum "
                "ON sefer_istatistik_mv (durum)"
            )
        )

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_db_engine, temp_db_url, monkeypatch):
    AsyncTestingSessionLocal = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    session = AsyncTestingSessionLocal()

    # Monkeypatch for components using the global pool
    # We use a NonClosingSession wrapper to prevent components from closing our test session
    class NonClosingSession:
        def __init__(self, session):
            self._session = session

        def __call__(self):
            return self

        async def __aenter__(self):
            return self._session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Do NOT close the session here, let the fixture handle it
            pass

        def __getattr__(self, name):
            return getattr(self._session, name)

    wrapper = NonClosingSession(session)
    monkeypatch.setattr("app.database.connection.AsyncSessionLocal", wrapper)
    monkeypatch.setattr("app.database.unit_of_work.AsyncSessionLocal", wrapper)

    # Sync support
    sync_url = temp_db_url.replace("+asyncpg", "")
    sync_engine = create_engine(sync_url)
    SyncTestingSessionLocal = sessionmaker(
        bind=sync_engine, autocommit=False, autoflush=False
    )
    monkeypatch.setattr(
        "app.database.connection.SyncSessionLocal", SyncTestingSessionLocal
    )

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


@pytest.fixture
def analiz_repo(db_session):
    from app.database.repositories.analiz_repo import AnalizRepository

    return AnalizRepository(session=db_session)


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
    from app.core.services.sefer_service import SeferService
    from app.database.repositories.sefer_repo import SeferRepository

    return SeferService(repo=SeferRepository(session=db_session))


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
        "hedef_tuketim": 30.5,
    }


@pytest.fixture
def sample_sofor_data():
    return {
        "ad_soyad": "Ahmet Yılmaz",
        "telefon": "0532 123 45 67",
        "ehliyet_sinifi": "E",
        "ise_baslama_tarihi": date.today(),
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
        "baslangic_tarihi": datetime.now(timezone.utc),
        "bitis_tarihi": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_yakit_data():
    return {
        "arac_id": 1,
        "tarih": date.today(),
        "litre": Decimal("100.50"),
        "fiyat_tl": Decimal("40.25"),
        "km_sayac": 100500,
    }


@pytest.fixture
async def async_client(db_session):
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def auth_headers():
    """Admin/Superuser auth headers for tests via virtual super-admin token."""
    from datetime import timedelta

    from app.config import settings
    from app.core.security import create_access_token

    token = create_access_token(
        data={"sub": settings.SUPER_ADMIN_USERNAME, "is_super": True},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_auth_headers(auth_headers):
    return auth_headers


@pytest.fixture
async def normal_auth_headers(db_session):
    """Normal user auth headers for tests - Ensures testuser exists in DB"""
    from datetime import timedelta

    from sqlalchemy import select

    from app.core.security import create_access_token, get_password_hash
    from app.database.models import Kullanici, Rol

    # Ensure role exists
    role_result = await db_session.execute(select(Rol).where(Rol.ad == "izleyici"))
    role = role_result.scalar_one_or_none()
    if not role:
        role = Rol(ad="izleyici", yetkiler={"sefer:read": True})
        db_session.add(role)
        await db_session.flush()

    # Ensure test user exists
    result = await db_session.execute(
        select(Kullanici).where(Kullanici.email == "testuser@lojinext.test")
    )
    user = result.scalar_one_or_none()

    if not user:
        user = Kullanici(
            email="testuser@lojinext.test",
            sifre_hash=get_password_hash("userpassword"),
            ad_soyad="Regular User",
            rol_id=role.id,
            aktif=True,
        )
        db_session.add(user)
        await db_session.commit()

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def no_trip_read_auth_headers(db_session):
    """Auth headers for a user that does not have sefer:read permission."""
    from datetime import timedelta

    from sqlalchemy import select

    from app.core.security import create_access_token, get_password_hash
    from app.database.models import Kullanici, Rol

    role_name = "kisitli"
    role_result = await db_session.execute(select(Rol).where(Rol.ad == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        role = Rol(ad=role_name, yetkiler={"dashboard:read": True})
        db_session.add(role)
        await db_session.flush()

    user_email = "noread@lojinext.test"
    result = await db_session.execute(select(Kullanici).where(Kullanici.email == user_email))
    user = result.scalar_one_or_none()
    if not user:
        user = Kullanici(
            email=user_email,
            sifre_hash=get_password_hash("userpassword"),
            ad_soyad="No Read User",
            rol_id=role.id,
            aktif=True,
        )
        db_session.add(user)
    elif user.rol_id != role.id:
        user.rol_id = role.id

    await db_session.commit()

    token = create_access_token(
        data={"sub": user_email},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}
