import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user, AuthServiceDep
from app.config import settings
from app.infrastructure.security import jwt_handler
from app.database.models import Kullanici
from app.infrastructure.resilience.rate_limiter import rate_limited
from app.infrastructure.logging.logger import get_logger
from app.schemas.user import KullaniciRead

router = APIRouter()
logger = get_logger(__name__)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@router.post("/token", name="auth:login", response_model=Token)
@rate_limited("auth_token", rate=5.0, period=1.0)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
):
    """Elite Login using AuthService."""
    # ── SUPER ADMIN BYPASS ──────────────────────────────────
    super_admin_user = settings.SUPER_ADMIN_USERNAME
    super_admin_pass = (
        settings.SUPER_ADMIN_PASSWORD.get_secret_value()
        if settings.SUPER_ADMIN_PASSWORD
        else (
            settings.ADMIN_PASSWORD.get_secret_value()
            if hasattr(settings, "ADMIN_PASSWORD") and settings.ADMIN_PASSWORD
            else None
        )
    )

    if (
        super_admin_pass
        and form_data.username == super_admin_user
        and secrets.compare_digest(form_data.password, super_admin_pass)
    ):
        # Virtual tokens for superadmin
        access_token = jwt_handler.create_access_token(
            data={"sub": super_admin_user, "role": "super_admin", "is_super": True}
        )
        refresh_token = jwt_handler.create_refresh_token(
            data={"sub": super_admin_user, "is_super": True}
        )
        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    if form_data.username == super_admin_user and not super_admin_pass:
        logger.warning(
            "SUPER_ADMIN_PASSWORD is not configured; bypass auth is disabled."
        )

    # ── REGULAR AUTH ──────────────────────────────────────────
    access_token, refresh_token = await auth_service.authenticate(
        form_data.username, form_data.password, request
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
    auth_service: AuthServiceDep,
):
    """Elite Logout using AuthService and revocation."""
    await auth_service.revoke_session(current_user.id)
    return {"detail": "Successfully logged out"}


@router.post("/refresh", name="auth:refresh", response_model=Token)
async def refresh_access_token(refresh_token: str, auth_service: AuthServiceDep):
    """Elite Token Refresh."""
    access_token, refresh_token = await auth_service.refresh_session(refresh_token)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=KullaniciRead)
async def read_users_me(
    current_user: Annotated[Kullanici, Depends(get_current_user)],
):
    """Mevcut kullanıcı bilgilerini getir"""
    return current_user


@router.post("/password-reset-request")
@rate_limited("pw_reset_req", rate=2.0, period=60.0)
async def request_password_reset(
    data: PasswordResetRequest, auth_service: AuthServiceDep
):
    """Password reset token generation logic."""
    token = await auth_service.request_password_reset(data.email)

    # Security: Always return 200 to prevent email enumeration
    if token and settings.ENVIRONMENT != "prod":
        return {"detail": "Reset token generated", "token": token}

    return {
        "detail": "Eğer e-posta adresi kayıtlı ise sıfırlama talimatı gönderilmiştir."
    }


@router.post("/password-reset-confirm")
async def confirm_password_reset(
    data: PasswordResetConfirm, auth_service: AuthServiceDep
):
    """Password reset execution."""
    success = await auth_service.reset_password(data.token, data.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş token")

    return {"detail": "Şifreniz başarıyla güncellendi"}
