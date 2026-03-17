import sys
from contextlib import ExitStack
from unittest.mock import MagicMock
from unittest import mock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import UserDefinedType

# Mock problematic dependencies globally for tests (that don't affect logic)
sys.modules["sentry_sdk"] = MagicMock()
sys.modules["sentry_sdk.integrations"] = MagicMock()
sys.modules["sentry_sdk.integrations.fastapi"] = MagicMock()
sys.modules["sentry_sdk.integrations.sqlalchemy"] = MagicMock()
sys.modules["groq"] = MagicMock()
sys.modules["shapely"] = MagicMock()
sys.modules["shapely.geometry"] = MagicMock()
sys.modules["prometheus_fastapi_instrumentator"] = MagicMock()

# --- PREVENT ML MODEL CACHE LOADING IN TESTS ---
from unittest.mock import patch  # noqa: E402


def mock_load_model(self, *args, **kwargs):
    raise RuntimeError("Loading mocked out for tests")


patch(
    "app.core.ml.ensemble_predictor.EnsembleFuelPredictor.load_model",
    new=mock_load_model,
).start()


class MockGeometry(UserDefinedType):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def get_col_spec(self, **kw):
        return "TEXT"

    def bind_processor(self, dialect):
        def process(value):
            return value

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return value

        return process


sys.modules["geoalchemy2"] = MagicMock()
sys.modules["geoalchemy2"].Geometry = MockGeometry
sys.modules["geoalchemy2.shape"] = MagicMock()

# PostgreSQL Configuration from app config
from app.config import settings  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

# Override database URL for tests
TEST_DATABASE_URL = str(settings.DATABASE_URL).replace("tir_yakit", "tir_yakit_test")


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Session scoped engine to avoid attached to a different loop errors."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
def db_session_factory(db_engine):
    """Session scoped session maker that also patches the globally used SessionLocals."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    # CRITICAL: Patch AsyncSessionLocal when the factory is created
    import app.database.connection  # noqa: E402
    import app.database.unit_of_work  # noqa: E402

    app.database.connection.AsyncSessionLocal = factory
    app.database.unit_of_work.AsyncSessionLocal = factory

    return factory


@pytest_asyncio.fixture(scope="function")
async def setup_test_db(db_engine, db_session_factory):
    from app.database.models import (
        Base,
        Rol,
        Kullanici,
    )
    from app.main import app
    from app.api.deps import get_db
    from app.core.security import get_password_hash

    async def override_get_db():
        async with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    print("\n--- DEBUG: setup_test_db starting ---")
    async with db_engine.begin() as conn:
        # Re-create all tables in the test database
        print("Dropping tables...")
        await conn.execute(text("DROP TABLE IF EXISTS lokasyonlar CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS seferler CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS araclar CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS soforler CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS yakit_alimlari CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS kullanicilar CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS roller CASCADE"))

        print("Creating tables via Base.metadata.create_all...")
        await conn.run_sync(Base.metadata.create_all)

        # Verify columns of lokasyonlar
        print("Verifying lokasyonlar columns...")
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'lokasyonlar'"
            )
        )
        cols = [r[0] for r in result.fetchall()]
        print(f"Columns in 'lokasyonlar': {cols}")
    print("--- DEBUG: setup_test_db finished ---\n")

    # Seed mandatory users for tests
    async with db_session_factory() as session:
        # Create Roles
        super_rol = Rol(ad="super_admin", yetkiler={"*": True})
        user_rol = Rol(ad="user", yetkiler={"read": True, "write": True})
        session.add_all([super_rol, user_rol])
        await session.commit()
        await session.refresh(super_rol)
        await session.refresh(user_rol)

        # Create Users
        admin_user = Kullanici(
            email=settings.SUPER_ADMIN_USERNAME,
            ad_soyad="Test Admin",
            sifre_hash=get_password_hash("test_pass"),
            rol_id=super_rol.id,
            aktif=True,
        )
        normal_user = Kullanici(
            email="user@example.com",
            ad_soyad="Test User",
            sifre_hash=get_password_hash("test_pass"),
            rol_id=super_rol.id,
            aktif=True,
        )
        session.add_all([admin_user, normal_user])
        await session.commit()

    yield
    app.dependency_overrides.clear()
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(db_session_factory, setup_test_db):
    """Async database session fixture (requires setup_test_db implicitly)"""
    async with db_session_factory() as session:
        yield session
        await session.rollback()


# ============== API TEST FIXTURES ==============


@pytest.fixture(scope="function")
def client():
    """FastAPI TestClient fixture (Sync)"""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def async_client():
    """Async FastAPI TestClient fixture"""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def async_superuser_token_headers(async_client):
    """Admin token simulation"""
    from app.infrastructure.security.jwt_handler import create_access_token

    token = create_access_token(
        data={"sub": settings.SUPER_ADMIN_USERNAME, "typ": "access", "is_super": True}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def async_normal_user_token_headers(async_client):
    """Normal user token simulation"""
    from app.infrastructure.security.jwt_handler import create_access_token

    token = create_access_token(data={"sub": "user@example.com", "typ": "access"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def mocker():
    """Minimal pytest-mock compatible fixture for legacy tests."""

    class SimpleMocker:
        Mock = mock.Mock
        MagicMock = mock.MagicMock
        AsyncMock = mock.AsyncMock
        call = mock.call
        ANY = mock.ANY

        def __init__(self):
            self._stack = ExitStack()

        def patch(self, target, *args, **kwargs):
            return self._stack.enter_context(mock.patch(target, *args, **kwargs))

        def patch_object(self, target, attribute, *args, **kwargs):
            return self._stack.enter_context(
                mock.patch.object(target, attribute, *args, **kwargs)
            )

        def spy(self, obj, name):
            original = getattr(obj, name)
            wrapper = mock.Mock(wraps=original)
            self._stack.enter_context(mock.patch.object(obj, name, wrapper))
            return wrapper

        def stopall(self):
            self._stack.close()

    fixture = SimpleMocker()
    try:
        yield fixture
    finally:
        fixture.stopall()


@pytest_asyncio.fixture(scope="function")
async def sofor_id(db_session_factory, setup_test_db):
    """Seed a disposable driver record for legacy delete smoke tests."""
    from app.database.models import Sofor

    async with db_session_factory() as session:
        sofor = Sofor(
            ad_soyad="Delete Test Driver",
            telefon="05000000000",
            ehliyet_sinifi="E",
            aktif=True,
            is_deleted=False,
        )
        session.add(sofor)
        await session.commit()
        await session.refresh(sofor)
        yield sofor.id
