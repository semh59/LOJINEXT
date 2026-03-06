from typing import List
from datetime import datetime
from sqlalchemy import select, and_
from app.database.base_repository import BaseRepository
from app.database.models import AracBakim


class MaintenanceRepository(BaseRepository[AracBakim]):
    """Repository for managing vehicle maintenance records."""

    async def get_by_arac_id(self, arac_id: int) -> List[AracBakim]:
        """Fetch all maintenance records for a specific vehicle."""
        stmt = (
            select(AracBakim)
            .where(AracBakim.arac_id == arac_id)
            .order_by(AracBakim.bakim_tarihi.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_maintenance(self) -> List[AracBakim]:
        """Fetch maintenance records that are not yet marked as completed."""
        stmt = (
            select(AracBakim)
            .where(AracBakim.tamamlandi.is_(False))
            .order_by(AracBakim.bakim_tarihi.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming_maintenance(self) -> List[AracBakim]:
        """Fetch maintenance records scheduled within the next N days."""
        now = datetime.now()
        stmt = (
            select(AracBakim)
            .where(and_(AracBakim.bakim_tarihi >= now, AracBakim.tamamlandi.is_(False)))
            .order_by(AracBakim.bakim_tarihi.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
