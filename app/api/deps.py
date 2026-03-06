from datetime import datetime, timezone
from typing import Annotated, Union, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.services.security_service import Permission, SecurityService
from app.core.services.weather_service import WeatherService, get_weather_service
from app.database.connection import get_db
from app.database.models import Kullanici, Rol
from app.infrastructure.logging.logger import get_logger
from app.database.unit_of_work import UnitOfWork, get_uow
from app.core.services.auth_service import AuthService
from app.infrastructure.background.job_manager import (
    get_job_manager,
    BackgroundJobManager,
)

logger = get_logger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]
WeatherServiceDep = Annotated[WeatherService, Depends(get_weather_service)]
UOWDep = Annotated[UnitOfWork, Depends(get_uow)]


async def get_auth_service(uow: UOWDep) -> AuthService:
    return AuthService(uow)


async def get_background_job_manager() -> BackgroundJobManager:
    return get_job_manager()


async def get_arac_service(uow: UOWDep):
    from app.core.services.arac_service import AracService

    return AracService(repo=uow.arac_repo)


async def get_sofor_service(uow: UOWDep):
    from app.core.services.sofor_service import SoforService

    return SoforService(repo=uow.sofor_repo)


async def get_sefer_service(uow: UOWDep):
    from app.core.services.sefer_service import SeferService

    return SeferService(repo=uow.sefer_repo)


async def get_yakit_service(uow: UOWDep):
    from app.core.services.yakit_service import YakitService

    return YakitService(repo=uow.yakit_repo)


async def get_lokasyon_service(uow: UOWDep):
    from app.core.services.lokasyon_service import LokasyonService

    return LokasyonService(repo=uow.lokasyon_repo)


async def get_dorse_service(uow: UOWDep):
    from app.core.services.dorse_service import DorseService

    logger.error(f"[DEBUG] Type of UOW: {type(uow)}")
    logger.error(f"[DEBUG] DIR of UOW: {dir(uow)}")
    if not hasattr(uow, "event_bus"):
        logger.critical(
            "[CRITICAL] UOW DOES NOT HAVE EVENT BUS! Fetching from singleton..."
        )
        from app.infrastructure.events.event_bus import get_event_bus

        return DorseService(repo=uow.dorse_repo, event_bus=get_event_bus())

    return DorseService(repo=uow.dorse_repo, event_bus=uow.event_bus)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(db: SessionDep, token: TokenDep) -> Kullanici:
    try:
        # Phase 3 Security: Add leeway for clock skew
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
            options={"leeway": 60},
        )
        username: str = payload.get("sub")
        is_super: bool = payload.get("is_super", False)

        if username is None:
            logger.warning("Token validation failed: Missing subject (sub)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        if is_super and username == settings.SUPER_ADMIN_USERNAME:
            logger.info(f"Super admin access granted: {username}")

            # Create a virtual Rol for the superadmin
            super_role = Rol(
                id=0,
                ad="super_admin",
                yetkiler={"*": True},
                olusturma=datetime.now(timezone.utc),
            )

            virtual_user = Kullanici(
                id=None,
                email=f"{username}@lojinext.internal"
                if "@" not in username
                else username,
                ad_soyad="Super Administrator",
                rol_id=0,
                rol=super_role,
                aktif=True,
                sifre_hash="",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                son_giris=datetime.now(timezone.utc),
            )
            return virtual_user

    except jwt.ExpiredSignatureError:
        logger.warning(f"Signature has expired for token: {token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.warning(f"Token decoding failed or other error: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Kullanici)
        .options(selectinload(Kullanici.rol))
        .where(Kullanici.email == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"Authenticated user not found in DB: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    if not user.aktif:
        logger.warning(f"Inactive user attempted access: {username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_active_admin(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
) -> Kullanici:
    """RBAC check for ADMIN level access."""
    SecurityService.verify_permission(current_user, Permission.ADMIN)
    return current_user


async def get_current_superadmin(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
) -> Kullanici:
    """RBAC check for SUPERADMIN level access."""
    SecurityService.verify_permission(current_user, Permission.SUPERADMIN)
    return current_user


def require_permissions(required_permission: Union[Permission, str, List[str]]):
    """
    FastAPI dependency injection factory for granular RBAC controls.
    Kullanım: current_user: Kullanici = Depends(require_permissions("sefer:write"))
    """

    async def permission_checker(
        current_user: Annotated[Kullanici, Depends(get_current_user)],
    ) -> Kullanici:
        SecurityService.verify_permission(current_user, required_permission)
        return current_user

    return permission_checker
