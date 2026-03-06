import threading
from typing import Any, List, Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.database.models import SistemKonfig, KonfigGecmis


class AdminConfigRepository(BaseRepository[SistemKonfig]):
    """
    Elite Configuration Repository for System Parameters.
    Handles dynamic values and change history.
    """

    model = SistemKonfig

    async def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        """Get full configuration record by key as dict."""
        session = self.session
        config = await session.get(SistemKonfig, key)
        return self._to_dict(config) if config else None

    async def get_value(self, key: str, default: Any = None) -> Any:
        """Get only the value (deger) for a key."""
        config = await self.get_config(key)
        return config["deger"] if config else default

    async def update_value(
        self,
        key: str,
        new_value: Any,
        updated_by_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update configuration value and log to history.
        """
        session = self.session
        config = await session.get(SistemKonfig, key)
        if not config:
            raise ValueError(f"Konfigrasyon anahtarı bulunamadı: {key}")

        old_value = config.deger
        config.deger = new_value
        config.guncelleyen_id = updated_by_id

        history = KonfigGecmis(
            anahtar=key,
            eski_deger=old_value,
            yeni_deger=new_value,
            degisiklik_sebebi=reason,
            guncelleyen_id=updated_by_id
            if updated_by_id and updated_by_id > 0
            else None,
        )
        session.add(history)

        if not self.session:
            await session.commit()

        # Refresh is not strictly needed for dict conversion but good for consistency
        await session.refresh(config)
        return self._to_dict(config)

    async def get_by_group(self, group: str) -> List[Dict[str, Any]]:
        """Get all configurations in a specific group as dicts."""
        session = self.session
        stmt = select(SistemKonfig).where(SistemKonfig.grup == group)
        result = await session.execute(stmt)
        return [self._to_dict(o) for o in result.scalars().all()]

    async def get_history(self, key: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get change history for a key as dicts."""
        session = self.session
        stmt = (
            select(KonfigGecmis)
            .where(KonfigGecmis.anahtar == key)
            .order_by(KonfigGecmis.zaman.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        # KonfigGecmis is not the main model of this repo, so _to_dict won't work automatically
        # for it unless we use inspect(KonfigGecmis).
        # Let's use a manual conversion or create a separate repo for history.
        # For now, manual:
        from sqlalchemy import inspect

        mapper = inspect(KonfigGecmis).mapper
        return [
            {c.key: getattr(o, c.key) for c in mapper.column_attrs}
            for o in result.scalars().all()
        ]


# Thread-safe Singleton
_admin_config_repo_lock = threading.Lock()
_admin_config_repo: Optional[AdminConfigRepository] = None


def get_admin_config_repo(
    session: Optional[AsyncSession] = None,
) -> AdminConfigRepository:
    """AdminConfigRepo Provider."""
    global _admin_config_repo
    if session:
        return AdminConfigRepository(session=session)
    with _admin_config_repo_lock:
        if _admin_config_repo is None:
            _admin_config_repo = AdminConfigRepository()
    return _admin_config_repo
