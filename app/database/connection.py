import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

from sqlalchemy.engine.url import make_url

# ============================================================================
# ENGINE CONFIGURATION
# ============================================================================

# Database URL parsing
db_url = make_url(settings.DATABASE_URL)
is_sqlite = db_url.drivername.startswith("sqlite")

# SECURITY: Prevent sensitive data logging
# We explicitly check for 'true' to avoid accidental enabling
sql_echo = os.getenv("SQL_ECHO", "False").lower() == "true"

# Common Engine Arguments
engine_args = {
    "echo": sql_echo,
    "future": True,
    "pool_pre_ping": True,
}

if is_sqlite:
    # SQLite concurrency improvement
    engine_args["connect_args"] = {"timeout": 30}

if not is_sqlite:
    # PostgreSQL specific pool settings
    # Hardened pool settings for production-grade reliability
    engine_args.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })
    
    # SECURITY: SSL/TLS for production environment
    if settings.ENVIRONMENT == "prod":
        engine_args["connect_args"] = {"ssl": "require"}

# Create Async Engine
# SECURITY: Ensure asyncpg driver is used for async operations if it's postgres
async_url = db_url
if "postgresql" in async_url.drivername and "+asyncpg" not in async_url.drivername:
    async_url = async_url.set(drivername="postgresql+asyncpg")

engine = create_async_engine(async_url, **engine_args)
# Add safety marker to identify this as an ASYNC engine
try:
    engine.pool.info["engine_type"] = "async"
except (AttributeError, TypeError):
    # Some pools (like StaticPool) might not support .info easily
    # or handle it differently in specific versions.
    pass

# Create Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency: Yields an async database session.
    Handles rollback automatically on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


# ============================================================================
# SYNC WRAPPER - Core Services Compatibility (Legacy Support)
# ============================================================================
# Bu wrapper eski senkron kodun PostgreSQL'e erişmesini sağlar.
# Yeni kod için ASYNC versiyonları kullanın.

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Sync Engine (core services için)
# Using make_url for safer conversion
sync_url = db_url
if "+asyncpg" in sync_url.drivername:
    sync_url = sync_url.set(drivername=sync_url.drivername.replace("+asyncpg", ""))

# Sync engine pool settings
sync_engine_args = {
    "echo": os.getenv("SQL_ECHO", "False").lower() == "true",
    "pool_pre_ping": True,
}

# Add pool settings for non-SQLite databases
if not is_sqlite:
    sync_engine_args.update({
        "pool_size": 10,
        "max_overflow": 5,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })
    # SECURITY: SSL/TLS for production environment
    if settings.ENVIRONMENT == "prod":
        sync_engine_args["connect_args"] = {"ssl": "require"}

sync_engine = create_engine(sync_url, **sync_engine_args)
# Add safety marker to identify this as a SYNC engine
try:
    sync_engine.pool.info["engine_type"] = "sync"
except (AttributeError, TypeError):
    pass

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


@contextmanager
def get_sync_session() -> Session:
    """
    Sync session context manager.
    Core services için PostgreSQL bağlantısı.
    
    Usage:
        with get_sync_session() as session:
            result = session.execute(query)
    """
    session = SyncSessionLocal()
    # Tag session for traceability
    try:
        session.info["engine_type"] = "sync"
    except (AttributeError, TypeError):
        pass
    try:
        yield session
        # Auto-commit on success for legacy compatibility
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Sync session error: {e}", exc_info=True)
        raise
    finally:
        session.close()

# Legacy alias for backward compatibility with db_manager.py
# DEPRECATED: Use get_sync_session directly
get_connection = get_sync_session
