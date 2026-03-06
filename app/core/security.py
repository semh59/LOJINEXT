from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt

from app.config import settings
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifre doğrulama - doğrudan bcrypt kullanarak (Python 3.14 uyumlu)"""
    try:
        if not plain_password or not hashed_password:
            return False
        # bcrypt.checkpw handles constant time comparison for the hash
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Şifre doğrulama başarısız (Potansiyel saldırı veya bozuk veri): {e!s}"
        )
        return False
    except Exception as e:
        logger.error(f"Beklenmeyen şifre doğrulama hatası: {e!s}")
        return False


def get_password_hash(password: str) -> str:
    """Şifre hash'leme - doğrudan bcrypt kullanarak (Python 3.14 uyumlu)"""
    # Güvenlik kontrolleri
    if not password:
        raise ValueError("Şifre boş olamaz")

    # bcrypt max 72 byte destekler - DoS önlemi
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Şifre çok uzun (maksimum 72 byte)")

    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM
    )
    return encoded_jwt
