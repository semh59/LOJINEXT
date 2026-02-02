from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.base_repository import BaseRepository
from app.database.models import Guzergah
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class GuzergahRepository(BaseRepository[Guzergah]):
    """Güzergah veritabanı operasyonları"""

    model = Guzergah

    async def get_all_active(self) -> List[Dict]:
        """Tüm aktif güzergahları getir"""
        query = (
            select(self.model).where(self.model.aktif == True).order_by(self.model.ad)
        )
        result = await self.session.execute(query)
        return [
            row.to_dict() if hasattr(row, "to_dict") else row.__dict__
            for row in result.scalars().all()
        ]

    async def create_guzergah(self, data: dict) -> Guzergah:
        """Yeni güzergah oluştur"""
        return await self.create(**data)

    async def update_guzergah(self, id: int, data: dict) -> bool:
        """Güzergah güncelle"""
        return await self.update(id, **data)

    async def soft_delete(self, id: int) -> bool:
        """Soft delete (aktif=False)"""
        return await self.update(id, aktif=False)


# Singleton Removal - Use Dependency Injection
# import threading
# _guzergah_repo_lock = threading.Lock()
# _guzergah_repo: Optional[GuzergahRepository] = None

# def get_guzergah_repo(session: Optional[AsyncSession] = None) -> GuzergahRepository:
#     if session:
#         return GuzergahRepository(session=session)
#     return GuzergahRepository() # Should generally avoid this without session
