from datetime import timedelta
from typing import Annotated

from app.api.deps import SessionDep
from app.config import settings
from app.core.security import create_access_token, verify_password
from app.database.models import Kullanici
from app.infrastructure.resilience.rate_limiter import rate_limited
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from app.api.deps import get_current_user
from app.schemas.user import KullaniciRead

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

@router.post("/token", response_model=Token)
@rate_limited("auth_token", rate=5.0, period=1.0)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep
):
    # ══════════════════════════════════════════════════════════════════════════
    # HARDCODED SUPER ADMIN - Database'de kayıtlı değil, sadece kod içinde
    # ══════════════════════════════════════════════════════════════════════════
    SUPER_ADMIN_USERNAME = "skara"
    SUPER_ADMIN_PASSWORD = "!23efe25ali!"
    
    if form_data.username == SUPER_ADMIN_USERNAME:
        if form_data.password == SUPER_ADMIN_PASSWORD:
            logger.info(f"Super admin login successful: {SUPER_ADMIN_USERNAME}")
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": SUPER_ADMIN_USERNAME, "role": "superadmin", "is_super": True},
                expires_delta=access_token_expires
            )
            return Token(access_token=access_token, token_type="bearer")
        else:
            logger.warning(f"Failed super admin login attempt for: {SUPER_ADMIN_USERNAME}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    # ══════════════════════════════════════════════════════════════════════════
    
    query = select(Kullanici).where(Kullanici.kullanici_adi == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Timing Attack Prevention: Always check a password hash even if user not found.
    # We use a dummy hash if user is None.
    dummy_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L6s57Wy60Q2i9ki"
    password_to_check = form_data.password
    hash_to_check = user.sifre_hash if user else dummy_hash

    is_valid = verify_password(password_to_check, hash_to_check)

    if not user or not is_valid:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Successful login for user: {user.kullanici_adi}")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.kullanici_adi, "role": user.rol},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=KullaniciRead)
async def read_users_me(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """Mevcut kullanıcı bilgilerini getir"""
    return current_user
