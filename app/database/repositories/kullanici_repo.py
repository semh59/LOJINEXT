"""
TIR Yakıt Takip - Kullanıcı Repository
Kullanıcı CRUD + Authentication (Bcrypt) + Rate Limiting
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import bcrypt
from dotenv import load_dotenv

from app.database.base_repository import BaseRepository
from app.infrastructure.logging.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


import threading

class LoginAttemptTracker:
    """
    Brute force koruması için giriş denemesi takibi.
    
    - 5 başarısız denemede hesap 15 dakika kilitlenir
    - Memory-based (uygulama restart'ında sıfırlanır)
    - Thread-safe implementation
    """

    MAX_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    def __init__(self):
        self._lock = threading.Lock()
        self._attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._locked_until: Dict[str, datetime] = {}

    def record_attempt(self, username: str, success: bool):
        """Giriş denemesini kaydet (Thread-safe)"""
        with self._lock:
            now = datetime.now()

            if success:
                # Başarılı giriş - geçmişi temizle
                self._attempts[username] = []
                if username in self._locked_until:
                    del self._locked_until[username]
            else:
                # Başarısız - listeye ekle
                self._attempts[username].append(now)

                # Son 15 dakikadaki denemeleri say
                cutoff = now - timedelta(minutes=self.LOCKOUT_MINUTES)
                recent = [t for t in self._attempts[username] if t > cutoff]
                self._attempts[username] = recent

                # Limit aşıldı mı?
                if len(recent) >= self.MAX_ATTEMPTS:
                    self._locked_until[username] = now + timedelta(minutes=self.LOCKOUT_MINUTES)
                    logger.warning(f"Account locked: {username} for {self.LOCKOUT_MINUTES} minutes")

    def is_locked(self, username: str) -> bool:
        """Hesap kilitli mi?"""
        if username not in self._locked_until:
            return False

        if datetime.now() > self._locked_until[username]:
            # Kilit süresi doldu
            del self._locked_until[username]
            self._attempts[username] = []
            return False

        return True

    def get_remaining_attempts(self, username: str) -> int:
        """Kalan deneme sayısı"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.LOCKOUT_MINUTES)
        recent = [t for t in self._attempts.get(username, []) if t > cutoff]
        return max(0, self.MAX_ATTEMPTS - len(recent))

    def get_lockout_remaining(self, username: str) -> int:
        """Kilitlilik saniye cinsinden ne kadar kaldı"""
        if username not in self._locked_until:
            return 0
        remaining = (self._locked_until[username] - datetime.now()).total_seconds()
        return max(0, int(remaining))


# Global tracker instance
_login_tracker = LoginAttemptTracker()

def get_login_tracker() -> LoginAttemptTracker:
    return _login_tracker


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Kullanici


class KullaniciRepository(BaseRepository[Kullanici]):
    """Kullanıcı veritabanı operasyonları (Async)"""

    model = Kullanici
    DEFAULT_ADMIN_USER = "skara"

    async def get_all(self, sadece_aktif: bool = False) -> List[Dict]:
        """Tüm kullanıcıları listele (skara hariç)"""
        stmt = select(self.model).where(self.model.kullanici_adi != self.DEFAULT_ADMIN_USER)

        if sadece_aktif:
            stmt = stmt.where(self.model.aktif == True)

        stmt = stmt.order_by(self.model.kullanici_adi)

        async with self._get_session() as session:
            result = await session.execute(stmt)
            return [self._to_dict(obj) for obj in result.scalars().all()]

    async def get_by_username(self, kullanici_adi: str) -> Optional[Dict]:
        """Kullanıcı adıyla getir"""
        async with self._get_session() as session:
            result = await session.execute(select(self.model).where(self.model.kullanici_adi == kullanici_adi))
            obj = result.scalar_one_or_none()
            return self._to_dict(obj)

    async def add(
        self,
        kullanici_adi: str,
        sifre: str,
        ad_soyad: str = "",
        rol: str = "user"
    ) -> int:
        """Yeni kullanıcı ekle (Bcrypt hashing ile)"""
        sifre_hash = bcrypt.hashpw(sifre.encode(), bcrypt.gensalt(rounds=12)).decode('utf-8')

        return await self.create(
            kullanici_adi=kullanici_adi,
            sifre_hash=sifre_hash,
            ad_soyad=ad_soyad,
            rol=rol,
            aktif=True
        )

    async def update_kullanici(self, id: int, **kwargs) -> bool:
        """Kullanıcı güncelle"""
        allowed = ["kullanici_adi", "ad_soyad", "rol", "aktif"]
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        # Şifre değişikliği varsa hash'le
        if "sifre" in kwargs and kwargs["sifre"]:
            updates["sifre_hash"] = bcrypt.hashpw(
                kwargs["sifre"].encode(),
                bcrypt.gensalt(rounds=12)
            ).decode('utf-8')

        return await self.update(id, **updates)

    async def verify_login(
        self,
        kullanici_adi: str,
        sifre: str
    ) -> Optional[Dict]:
        """
        Güvenli login doğrulama (Bcrypt + Rate Limiting).
        """
        tracker = get_login_tracker()

        # Kilit kontrolü
        if tracker.is_locked(kullanici_adi):
            remaining = tracker.get_lockout_remaining(kullanici_adi)
            logger.warning(f"Locked account login attempt: {kullanici_adi}")
            raise ValueError(f"Hesap kilitli. {remaining // 60} dk {remaining % 60} sn kaldı.")

        async with self._get_session() as session:
            # Kullanıcıyı bul
            stmt = select(self.model).where(self.model.kullanici_adi == kullanici_adi).where(self.model.aktif == True)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                tracker.record_attempt(kullanici_adi, success=False)
                remaining = tracker.get_remaining_attempts(kullanici_adi)
                logger.warning(f"Failed login: {kullanici_adi} ({remaining} attempts left)")
                return None

            stored_hash = user.sifre_hash

            try:
                # Legacy SHA-256 check ve migration
                if isinstance(stored_hash, str) and len(stored_hash) == 64 and not stored_hash.startswith('$2b$'):
                    import hashlib
                    if hashlib.sha256(sifre.encode()).hexdigest() == stored_hash:
                        # Auto-migrate to bcrypt
                        logger.info(f"Migrating user {kullanici_adi} to bcrypt")
                        new_hash = bcrypt.hashpw(sifre.encode(), bcrypt.gensalt(rounds=12)).decode('utf-8')

                        user.sifre_hash = new_hash
                        if not self.session:
                            await session.commit() # Object is attached, so commit updates it
                        valid = True
                    else:
                        valid = False
                else:
                    # Bcrypt check
                    if isinstance(stored_hash, str):
                        stored_hash_bytes = stored_hash.encode()
                    elif isinstance(stored_hash, memoryview):
                        stored_hash_bytes = bytes(stored_hash)
                    else:
                        stored_hash_bytes = stored_hash

                    valid = bcrypt.checkpw(sifre.encode(), stored_hash_bytes)

                if valid:
                    tracker.record_attempt(kullanici_adi, success=True)
                    user.son_giris = datetime.now()
                    if not self.session:
                        await session.commit()
                    return self._to_dict(user)
                else:
                    tracker.record_attempt(kullanici_adi, success=False)
                    remaining = tracker.get_remaining_attempts(kullanici_adi)
                    logger.warning(f"Failed login: {kullanici_adi} ({remaining} attempts left)")

            except Exception as e:
                logger.error(f"Login verification error: {e}", exc_info=True)

            return None

    async def create_default_admin(self):
        """Varsayılan admin hesabını oluştur veya güncelle"""
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
        if not default_password:
            # Silent return or logger warning if not set in dev, but enforced in prod?
            # User previously had issue logging in.
            if os.getenv("ENV") == "prod":
                 raise ValueError("DEFAULT_ADMIN_PASSWORD required in prod")
            return

        sifre_hash = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt(rounds=12)).decode('utf-8')

        async with self._get_session() as session:
            stmt = select(self.model).where(self.model.kullanici_adi == self.DEFAULT_ADMIN_USER)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.sifre_hash = sifre_hash
                existing.aktif = True
                logger.info(f"Updated default admin '{self.DEFAULT_ADMIN_USER}'")
            else:
                new_admin = self.model(
                    kullanici_adi=self.DEFAULT_ADMIN_USER,
                    sifre_hash=sifre_hash,
                    ad_soyad='Sistem Admin',
                    rol='admin',
                    aktif=True
                )
                session.add(new_admin)
                logger.info(f"Created default admin '{self.DEFAULT_ADMIN_USER}'")
            
            if not self.session:
                await session.commit()


# Thread-safe Singleton
_kullanici_repo_lock = threading.Lock()
_kullanici_repo: Optional[KullaniciRepository] = None

def get_kullanici_repo(session: Optional[AsyncSession] = None) -> KullaniciRepository:
    """KullaniciRepo Provider. Eğer session verilirse yeni instance döner (UoW için)."""
    global _kullanici_repo
    if session:
        return KullaniciRepository(session=session)
    with _kullanici_repo_lock:
        if _kullanici_repo is None:
            _kullanici_repo = KullaniciRepository()
    return _kullanici_repo
