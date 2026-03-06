from typing import List
from sqlalchemy import select
from app.database.base_repository import BaseRepository
from app.database.models import KullaniciOturumu


class SessionRepository(BaseRepository[KullaniciOturumu]):
    """
    Pure data access for User Sessions.
    """

    model = KullaniciOturumu

    async def get_active_sessions(self, kullanici_id: int) -> List[KullaniciOturumu]:
        """Get all currently active sessions for a user."""
        session = self.session
        stmt = select(self.model).where(
            self.model.kullanici_id == kullanici_id, self.model.aktif
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_all(self, kullanici_id: int):
        """Mark all sessions for a user as inactive."""
        session = self.session
        sessions = await self.get_active_sessions(kullanici_id)
        for s in sessions:
            s.aktif = False

        if not self.session:
            await session.commit()
