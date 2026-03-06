from typing import Optional
from sqlalchemy import select
from app.database.base_repository import BaseRepository
from app.database.models import Kullanici


class KullaniciRepository(BaseRepository[Kullanici]):
    """Kullanıcı veritabanı operasyonları (Async)"""

    model = Kullanici

    async def get_by_email(self, email: str) -> Optional[Kullanici]:
        """Email ile kullanıcı bul."""
        session = self.session
        stmt = select(self.model).where(self.model.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_reset_token(self, token: str) -> Optional[Kullanici]:
        """Sıfırlama token'ı ile kullanıcı bul."""
        session = self.session
        from datetime import datetime, timezone

        stmt = select(self.model).where(
            self.model.sifre_sifir_token == token,
            self.model.sifre_sifir_son > datetime.now(timezone.utc),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
