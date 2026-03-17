from typing import Optional, Tuple
from fastapi import HTTPException, Request, status
import datetime
from datetime import timezone

from app.database.models import KullaniciOturumu
from app.database.unit_of_work import UnitOfWork
from app.infrastructure.logging.logger import get_logger
from app.infrastructure.security import jwt_handler

logger = get_logger(__name__)


class AuthService:
    """Authentication and session management service."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def authenticate(
        self, email: str, password: str, request: Request
    ) -> Tuple[str, str]:
        """Authenticate user and create session."""
        async with self.uow:
            user = await self.uow.kullanici_repo.get_by_email(email)

            if user and user.kilitli_kadar:
                now = datetime.datetime.now(timezone.utc)
                if now < user.kilitli_kadar:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=(
                            "Cok fazla basarisiz deneme. Hesabiniz gecici olarak "
                            "kilitlenmistir. Lutfen 30 dakika sonra tekrar deneyin."
                        ),
                    )
                user.basarisiz_giris_sayisi = 0
                user.kilitli_kadar = None

            dummy_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6L6s57Wy60Q2i9ki"
            hash_to_check = user.sifre_hash if user else dummy_hash

            if not user or not jwt_handler.verify_password(password, hash_to_check):
                logger.warning(f"Failed login attempt: {email}")
                if user:
                    now = datetime.datetime.now(timezone.utc)
                    user.basarisiz_giris_sayisi += 1
                    if user.basarisiz_giris_sayisi >= 5:
                        user.kilitli_kadar = now + datetime.timedelta(minutes=30)
                    await self.uow.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Hatali e-posta veya sifre",
                )

            if user.basarisiz_giris_sayisi > 0:
                user.basarisiz_giris_sayisi = 0
                user.kilitli_kadar = None

            if not user.aktif:
                raise HTTPException(status_code=403, detail="Kullanici hesabi pasif")

        access_token = jwt_handler.create_access_token(
            data={"sub": user.email, "role": user.rol.ad if user.rol else "user"}
        )
        refresh_token = jwt_handler.create_refresh_token(data={"sub": user.email})

        access_payload = jwt_handler.decode_token(access_token)
        refresh_payload = jwt_handler.decode_token(refresh_token)

        async with self.uow:
            session = KullaniciOturumu(
                kullanici_id=user.id,
                access_token_hash=jwt_handler.get_password_hash(access_token),
                refresh_token_hash=jwt_handler.get_password_hash(refresh_token),
                ip_adresi=request.client.host if request.client else "0.0.0.0",
                tarayici=request.headers.get("user-agent"),
                access_bitis=datetime.datetime.fromtimestamp(
                    access_payload["exp"], tz=timezone.utc
                ),
                refresh_bitis=datetime.datetime.fromtimestamp(
                    refresh_payload["exp"], tz=timezone.utc
                ),
            )
            self.uow.session.add(session)

            user.son_giris = datetime.datetime.now(timezone.utc)
            user.son_giris_ip = session.ip_adresi

            await self.uow.commit()

        logger.info(f"Successful login: {user.email}")
        return access_token, refresh_token

    async def refresh_session(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token."""
        try:
            payload = jwt_handler.decode_token(refresh_token)
            if payload.get("typ") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            email = payload.get("sub")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        async with self.uow:
            user = await self.uow.kullanici_repo.get_by_email(email)
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            sessions = await self.uow.session_repo.get_active_sessions(user.id)
            target_session = None
            for session in sessions:
                if jwt_handler.verify_password(
                    refresh_token, session.refresh_token_hash
                ):
                    target_session = session
                    break

            if not target_session or target_session.refresh_bitis < datetime.datetime.now(
                timezone.utc
            ):
                raise HTTPException(
                    status_code=401, detail="Session expired or invalid"
                )

            access_token = jwt_handler.create_access_token(
                data={"sub": user.email, "role": user.rol.ad if user.rol else "user"}
            )

            target_session.access_token_hash = jwt_handler.get_password_hash(
                access_token
            )
            access_payload = jwt_handler.decode_token(access_token)
            target_session.access_bitis = datetime.datetime.fromtimestamp(
                access_payload["exp"], tz=timezone.utc
            )
            target_session.son_aktivite = datetime.datetime.now(timezone.utc)

            await self.uow.commit()

        return access_token, refresh_token

    async def revoke_session(self, user_id: int):
        """Immediately deactivate all active sessions for a user."""
        async with self.uow:
            await self.uow.session_repo.deactivate_all(user_id)
            await self.uow.commit()
        logger.info(f"Revoked all sessions for user id: {user_id}")

    async def request_password_reset(self, email: str) -> Optional[str]:
        """Generate reset token and store in DB."""
        import secrets
        from datetime import datetime, timedelta, timezone

        async with self.uow:
            user = await self.uow.kullanici_repo.get_by_email(email)
            if not user:
                return None

            token = secrets.token_urlsafe(32)
            user.sifre_sifir_token = token
            user.sifre_sifir_son = datetime.now(timezone.utc) + timedelta(hours=1)

            await self.uow.commit()

        logger.info(f"Password reset requested for: {email}")
        return token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Verify token and update password."""
        async with self.uow:
            user = await self.uow.kullanici_repo.get_by_reset_token(token)
            if not user:
                return False

            user.sifre_hash = jwt_handler.get_password_hash(new_password)
            user.sifre_sifir_token = None
            user.sifre_sifir_son = None
            user.sifre_degisim_tarihi = datetime.datetime.now(timezone.utc)

            await self.uow.session_repo.deactivate_all(user.id)
            await self.uow.commit()

        logger.info(f"Password successfully reset for user id: {user.id}")
        return True
