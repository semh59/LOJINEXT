"""
LojiNext AI - Dorse Repository
PostgreSQL CRUD operasyonları
"""

from typing import Any, Dict, Optional
import threading

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.database.models import Dorse
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class DorseRepository(BaseRepository[Dorse]):
    """Dorse veritabanı operasyonları (Async)"""

    model = Dorse
    search_columns = ["plaka", "tipi"]

    async def get_by_plaka(
        self, plaka: str, for_update: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Plaka ile dorse getir"""
        session = self.session
        stmt = select(self.model).where(self.model.plaka == plaka)
        if for_update:
            stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()
        return self._to_dict(obj) if obj else None


_dorse_repo_lock = threading.Lock()
_dorse_repo: Optional[DorseRepository] = None


def get_dorse_repo(session: Optional[AsyncSession] = None) -> DorseRepository:
    """DorseRepo Provider."""
    global _dorse_repo
    if session:
        return DorseRepository(session=session)
    with _dorse_repo_lock:
        if _dorse_repo is None:
            _dorse_repo = DorseRepository()
    return _dorse_repo
