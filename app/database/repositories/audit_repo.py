from typing import List
from sqlalchemy import select, and_
from app.database.base_repository import BaseRepository
from app.database.models import AdminAuditLog


class AuditRepository(BaseRepository[AdminAuditLog]):
    """
    Pure data access for Admin Audit Logs.
    """

    model = AdminAuditLog

    async def get_sefer_timeline(self, sefer_id: int) -> List[AdminAuditLog]:
        """Fetch all audit logs related to a specific trip for timeline construction."""
        stmt = (
            select(AdminAuditLog)
            .where(
                and_(
                    AdminAuditLog.hedef_tablo == "seferler",
                    AdminAuditLog.hedef_id == str(sefer_id),
                )
            )
            .order_by(AdminAuditLog.zaman.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
