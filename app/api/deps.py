from typing import Annotated
from jose import jwt, JWTError
from app.config import settings
from app.core.services.weather_service import WeatherService, get_weather_service
from app.database.connection import get_db
from app.database.models import Kullanici
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token"
)

SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]
WeatherServiceDep = Annotated[WeatherService, Depends(get_weather_service)]

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

async def get_current_user(db: SessionDep, token: TokenDep) -> Kullanici:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        is_super: bool = payload.get("is_super", False)
        role: str = payload.get("role", "user")
        
        if username is None:
            logger.warning("Token validation failed: Missing subject (sub)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        
        # ══════════════════════════════════════════════════════════════════════════
        # HARDCODED SUPER ADMIN - Database'de yok, sanal kullanıcı döndür
        # ══════════════════════════════════════════════════════════════════════════
        if is_super and username == "skara":
            logger.info(f"Super admin access granted: {username}")
            # Sanal Kullanici objesi oluştur (database'de yok ama API uyumlu)
            from datetime import datetime
            virtual_user = Kullanici(
                id=0,  # Sanal ID
                kullanici_adi="skara",
                ad_soyad="Super Administrator",
                rol="superadmin",
                aktif=True,
                sifre_hash="",  # Boş hash (güvenli - asla kullanılmaz)
            )
            # created_at için manuel set (ORM bypass)
            object.__setattr__(virtual_user, 'created_at', datetime.now())
            return virtual_user
        # ══════════════════════════════════════════════════════════════════════════
        
    except Exception as e:
        logger.warning(f"Token decoding failed or other error: {str(e)}")
        # Print for terminal visibility during debugging
        print(f"DEBUG AUTH: token={token[:20]}... error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )
    
    result = await db.execute(select(Kullanici).where(Kullanici.kullanici_adi == username))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"Authenticated user not found in DB: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    if not user.aktif:
        logger.warning(f"Inactive user attempted access: {username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_admin(
    current_user: Annotated[Kullanici, Depends(get_current_user)]
) -> Kullanici:
    # superadmin her şeye erişebilir
    if current_user.rol not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
