from app.config import settings

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

# Initialize Sentry before other imports
if settings.SENTRY_DSN and sentry_sdk:
    def pii_filter(event, hint):
        """Filters driver PII from events sent to Sentry."""
        if not settings.SENTRY_PII_FILTER:
            return event

        # Clear sensitive user info if any
        if "user" in event:
            event["user"] = {"id": "filtered"}

        # Sanitize breadcrumbs or log messages for common PII patterns (TCKN, Phone)
        # Turkish TCKN is 11 digits, Phone is usually 10-11
        import re

        pii_patterns = [
            r"\b\d{11}\b",  # TCKN
            r"\b\d{10,12}\b",  # Phone
        ]

        event_str = str(event)
        for pattern in pii_patterns:
            if re.search(pattern, event_str):
                # If PII detected, better to be safe and mask or drop
                # Simple implementation: mask in breadcrumbs if they exist
                if "breadcrumbs" in event:
                    for bc in event["breadcrumbs"].get("values", []):
                        if "message" in bc:
                            bc["message"] = re.sub(
                                pattern, "[PII_FILTERED]", bc["message"]
                            )

        return event

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0,
        before_send=pii_filter,
    )
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

from app.api.v1.api import api_router
from app.core.security import get_password_hash
from app.database.connection import engine
from app.database.models import Base, Kullanici
from app.infrastructure.logging.logger import setup_logging
from app.infrastructure.context.correlation_middleware import CorrelationMiddleware
from app.infrastructure.middleware.logging_middleware import RequestLoggingMiddleware
from app.infrastructure.middleware.rate_limit_middleware import RateLimitMiddleware
from app.core.errors import (
    BusinessException,
    business_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
try:
    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler
except ImportError:
    RateLimitExceeded = None
    _rate_limit_exceeded_handler = None
from app.api.middleware.rate_limiter import limiter
from app.infrastructure.cache.cache_invalidation import setup_cache_invalidation
from app.core.ai.rag_sync_service import get_rag_sync_service

logger = setup_logging()

if settings.SENTRY_DSN and not sentry_sdk:
    logger.warning("SENTRY_DSN is set but sentry-sdk is not installed.")
if settings.ENVIRONMENT != "test" and _OTEL_AVAILABLE:
    try:
        FastAPIInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        logger.info("OpenTelemetry instrumentation enabled.")
    except Exception as e:
        logger.warning(f"OpenTelemetry instrumentation failed: {e}")
elif settings.ENVIRONMENT != "test" and not _OTEL_AVAILABLE:
    logger.warning("OpenTelemetry paketleri yüklü değil; tracing devre dışı.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting up LojiNext AI Backend ({settings.ENVIRONMENT})...")
    seed_admin_email = settings.SUPER_ADMIN_USERNAME
    seed_admin_password = settings.ADMIN_PASSWORD.get_secret_value()

    # Initialize DB tables (Skip if managed by Alembic)
    if not settings.ALEMBIC_READY:
        logger.warning("ALEMBIC_READY is False. Using automatic table creation.")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized via create_all.")
    else:
        logger.info(
            "ALEMBIC_READY is True. Migrations are managed externally (Alembic)."
        )

    # Seed initial data (Admin user) - wrapped in try-except for bcrypt compatibility
    try:
        async with engine.begin():
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

            async_session = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                # Ensure 'super_admin' role exists
                from app.database.models import Rol
                session_changed = False

                stmt_rol = select(Rol).where(Rol.ad == "super_admin")
                result_rol = await session.execute(stmt_rol)
                rol_obj = result_rol.scalar_one_or_none()
                if not rol_obj:
                    logger.info("Seeding role: super_admin")
                    rol_obj = Rol(ad="super_admin", yetkiler={"*": True})
                    session.add(rol_obj)
                    await session.flush()  # Get ID
                    session_changed = True

                # Keep legacy databases aligned with new trip RBAC keys.
                role_defaults = {
                    "admin": {"sefer:read": True, "sefer:write": True},
                    "mudur": {"sefer:read": True},
                    "operafor": {"sefer:read": True},
                    "izleyici": {"sefer:read": True},
                }
                role_names = list(role_defaults.keys()) + ["superadmin", "super_admin"]
                roles_stmt = select(Rol).where(Rol.ad.in_(role_names))
                roles_result = await session.execute(roles_stmt)
                roles = {r.ad: r for r in roles_result.scalars().all()}

                for role_name, required_perms in role_defaults.items():
                    role = roles.get(role_name)
                    if not role:
                        continue
                    perms = dict(role.yetkiler or {})
                    changed = False
                    for perm_key, perm_value in required_perms.items():
                        if perms.get(perm_key) is not perm_value:
                            perms[perm_key] = perm_value
                            changed = True
                    if changed:
                        role.yetkiler = perms
                        session_changed = True
                        logger.info("Aligned role permissions: %s", role_name)

                for alias in ("superadmin", "super_admin"):
                    alias_role = roles.get(alias)
                    if not alias_role:
                        continue
                    perms = dict(alias_role.yetkiler or {})
                    if not perms.get("*") or "all" in perms:
                        perms.pop("all", None)
                        perms["*"] = True
                        alias_role.yetkiler = perms
                        session_changed = True
                        logger.info("Aligned %s wildcard permissions.", alias)

                # Check for a bootstrap admin stored in the email field.
                stmt = select(Kullanici).where(Kullanici.email == seed_admin_email)
                result = await session.execute(stmt)
                if not result.scalar_one_or_none():
                    logger.info(f"Seeding admin user: {seed_admin_email}")
                    admin_user = Kullanici(
                        email=seed_admin_email,
                        sifre_hash=get_password_hash(seed_admin_password),
                        ad_soyad="Sistem Yöneticisi",
                        rol_id=rol_obj.id,
                        aktif=True,
                    )
                    session.add(admin_user)
                    session_changed = True
                    logger.info(f"Admin user '{seed_admin_email}' created successfully.")
                else:
                    logger.debug(f"Admin user '{seed_admin_email}' already exists.")

                if session_changed:
                    await session.commit()
    except Exception as e:
        logger.warning(
            f"Admin seeding failed (bcrypt issue?): {e}. Continuing without admin user."
        )

    # Setup cache invalidation listeners
    setup_cache_invalidation()
    logger.info("Cache invalidation listeners registered.")

    # RAG Sync Service Başlat
    try:
        await get_rag_sync_service().initialize()
        logger.info("RAG Synchronization Service is active.")
    except Exception as e:
        logger.warning(f"RAG Sync failed to initialize: {e}")

    # Register Event Handlers
    from app.core.services.fuel_handler import register_fuel_handlers
    from app.core.handlers.model_training_handler import get_model_training_handler
    from app.core.handlers.physics_handler import get_physics_handler
    from app.core.services.notification_service import NotificationService
    from app.infrastructure.events.event_bus import get_event_bus, EventType

    register_fuel_handlers()
    get_model_training_handler().setup()
    get_physics_handler().register()

    # Register Notification Handlers
    notif_service = NotificationService()
    event_bus = get_event_bus()
    event_bus.subscribe(EventType.SEFER_UPDATED, notif_service.handle_event)
    event_bus.subscribe(EventType.SLA_DELAY, notif_service.handle_event)
    event_bus.subscribe(EventType.ANOMALY_DETECTED, notif_service.handle_event)

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

    from app.services.external_service import get_external_service

    await get_external_service().close()
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="TIR Yakıt Takip Sistemi Backend API",
    lifespan=lifespan,
)

if getattr(settings, "ENABLE_PROMETHEUS_METRICS", False):
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(app)
        logger.info("Prometheus metrics initialized at /metrics")
    except ImportError:
        logger.warning(
            "prometheus-fastapi-instrumentator not installed, metrics disabled."
        )

app.add_middleware(CorrelationMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=600 if settings.ENVIRONMENT == "dev" else 120,
)  # 600 req/min in dev

# CORS Policy Hardening
if settings.ENVIRONMENT == "prod":
    if not settings.CORS_ORIGINS or "*" in settings.CORS_ORIGINS:
        logger.error("CRITICAL SECURITY RISK: CORS_ORIGINS is '*' or empty in PROD!")
        raise RuntimeError(
            "CORS wildcard ('*') is FORBIDDEN in Production environment! Startup aborted for security purposes."
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
if RateLimitExceeded and _rate_limit_exceeded_handler:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
else:
    logger.warning("slowapi is not installed; global rate-limit exception handler disabled.")
app.state.limiter = limiter

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "LojiNext AI Backend is running", "docs": "/docs"}
