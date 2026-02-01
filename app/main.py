from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.config import settings
from app.database.connection import engine
from app.database.models import Base, Kullanici
from app.core.security import get_password_hash
from app.infrastructure.logging.logger import setup_logging
from sqlalchemy import select

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting up LojiNext AI Backend ({settings.ENVIRONMENT})...")

    # Initialize DB tables (Skip if managed by Alembic)
    if not settings.ALEMBIC_READY:
        logger.warning("ALEMBIC_READY is False. Using automatic table creation.")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized via create_all.")
    else:
        logger.info("ALEMBIC_READY is True. Migrations are managed externally (Alembic).")

    # Seed initial data (Admin user) - wrapped in try-except for bcrypt compatibility
    try:
        async with engine.begin() as conn:
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
            async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                # Check for 'skara' admin
                stmt = select(Kullanici).where(Kullanici.kullanici_adi == "skara")
                result = await session.execute(stmt)
                if not result.scalar_one_or_none():
                    logger.info("Seeding admin user: skara")
                    admin_user = Kullanici(
                        kullanici_adi="skara",
                        sifre_hash=get_password_hash("!23efe25ali!"),
                        ad_soyad="Sistem Yöneticisi",
                        rol="admin",
                        aktif=True
                    )
                    session.add(admin_user)
                    await session.commit()
                    logger.info("Admin user 'skara' created successfully.")
                else:
                    logger.debug("Admin user 'skara' already exists.")
    except Exception as e:
        logger.warning(f"Admin seeding failed (bcrypt issue?): {e}. Continuing without admin user.")

    # Setup cache invalidation listeners
    from app.infrastructure.cache.cache_invalidation import setup_cache_invalidation
    setup_cache_invalidation()
    logger.info("Cache invalidation listeners registered.")

    yield

    # Shutdown
    logger.info("Shutting down LojiNext Backend...")
    
    # AI Cleanup
    try:
        from app.core.ai.rag_engine import get_rag_engine
        get_rag_engine().save_to_disk()
        logger.info("RAG index saved to disk.")
    except Exception as e:
        logger.warning(f"RAG save failed during shutdown: {e}")

    try:
        from app.core.ai.qwen_chatbot import get_chatbot
        chatbot = get_chatbot(load_model=False)
        if chatbot.model_loaded:
            chatbot.unload_model()
    except Exception as e:
        logger.warning(f"Chatbot unload failed during shutdown: {e}")

    from app.services.external_service import get_external_service
    await get_external_service().close()
    await engine.dispose()
    logger.info("Shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="TIR Yakıt Takip Sistemi Backend API",
    lifespan=lifespan
)

# Enterprise Logging Middleware
from app.infrastructure.middleware.logging_middleware import RequestLoggingMiddleware
from app.infrastructure.middleware.rate_limit_middleware import RateLimitMiddleware

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)  # 120 req/min per IP

# CORS Policy Hardening
if settings.ENVIRONMENT == "prod":
    if not settings.CORS_ORIGINS or "*" in settings.CORS_ORIGINS:
        logger.error("CRITICAL SECURITY RISK: CORS_ORIGINS is '*' or empty in PROD!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Exception Handlers (Global Error Management)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.errors import (
    global_exception_handler, 
    business_exception_handler, 
    validation_exception_handler, 
    http_exception_handler,
    BusinessException
)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "LojiNext AI Backend is running", "docs": "/docs"}
