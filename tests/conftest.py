import pytest
import pytest_asyncio
from app.database.connection import AsyncSessionLocal
import asyncio

# Redefine event_loop to be session scoped because DB engine is global/module scoped
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Async database session fixture"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


# ============== API TEST FIXTURES ==============

@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture"""
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client) -> dict:
    """Admin kullanıcı için auth headers - DB'den bağımsız çalışır"""
    from app.config import settings
    
    # Önce gerçek admin ile login dene
    login_data = {
        "username": "admin",
        "password": settings.ADMIN_PASSWORD,
    }
    response = client.post("/api/v1/auth/token", data=login_data)
    
    if response.status_code == 200:
        tokens = response.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Admin yoksa manuel JWT token oluştur (test için)
    from app.core.security import create_access_token
    from datetime import timedelta
    
    access_token = create_access_token(
        data={"sub": "admin", "role": "admin"},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="module")
def normal_user_token_headers(client) -> dict:
    """Normal kullanıcı için auth headers"""
    from app.config import settings
    from app.core.security import create_access_token
    from datetime import timedelta
    
    # Önce gerçek kullanıcı ile login dene
    login_data = {
        "username": "testuser",
        "password": "testpassword123",
    }
    response = client.post("/api/v1/auth/token", data=login_data)
    
    if response.status_code == 200:
        tokens = response.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Yoksa manuel token oluştur (role=user)
    access_token = create_access_token(
        data={"sub": "testuser", "role": "user"},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}

