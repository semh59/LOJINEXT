from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import IceriAktarimGecmisi
from app.database.repositories.base import BaseRepository


class ImportHistoryRepository(BaseRepository[IceriAktarimGecmisi]):
    """Repository for managing IceriAktarimGecmisi records."""

    def __init__(self, session: AsyncSession):
        super().__init__(IceriAktarimGecmisi, session)

    async def create_import_job(self, data: Dict[str, Any]) -> IceriAktarimGecmisi:
        """Create a new import job tracking record."""
        return await self.create(data)

    async def get_by_id(self, history_id: int) -> Optional[IceriAktarimGecmisi]:
        return await self.get(history_id)

    async def get_recent_jobs(self, limit: int = 50) -> List[IceriAktarimGecmisi]:
        """Fetch recent import jobs for administrative audit."""
        stmt = (
            select(IceriAktarimGecmisi)
            .order_by(IceriAktarimGecmisi.baslama_zamani.desc())
            .limit(limit)
        )
        result = await self._get_session().execute(stmt)
        return list(result.scalars().all())

    async def update_job_status(
        self, history_id: int, durum: str, **kwargs
    ) -> Optional[IceriAktarimGecmisi]:
        """Update job statistics and status safely."""
        update_data = {"durum": durum, **kwargs}
        return await self.update(history_id, update_data)


def get_import_history_repo(session: AsyncSession) -> ImportHistoryRepository:
    return ImportHistoryRepository(session)
