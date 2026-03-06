"""
TIR Yakıt Takip - Konfigürasyon Repository
Sistem ayarları (key-value) yönetimi
"""

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database.base_repository import BaseRepository
from app.database.models import Ayarlar


class ConfigRepository(BaseRepository[Ayarlar]):
    """Ayarlar tablosu veritabanı operasyonları (Async)"""

    model = Ayarlar

    async def get_value(self, key: str, default: Any = None) -> Any:
        """Ayar değerini getir"""
        session = self.session
        stmt = select(self.model.deger).where(self.model.anahtar == key)
        result = await session.execute(stmt)
        val = result.scalar_one_or_none()
        return val if val is not None else default

    async def set_value(self, key: str, value: Any, description: str = "") -> None:
        """Ayar değerini kaydet/güncelle (Upsert)"""
        session = self.session
        stmt = (
            insert(self.model)
            .values(anahtar=key, deger=str(value), aciklama=description)
            .on_conflict_do_update(
                index_elements=["anahtar"],
                set_={"deger": str(value), "aciklama": description},
            )
        )
        await session.execute(stmt)
        if not self.session:
            await session.commit()

    async def get_all_settings(self) -> Dict[str, Any]:
        """Tüm ayarları dict olarak getir"""
        settings = await self.get_all()
        return {s["anahtar"]: s["deger"] for s in settings}


# Thread-safe Singleton
import threading

from sqlalchemy.ext.asyncio import AsyncSession

_config_repo_lock = threading.Lock()
_config_repo: Optional[ConfigRepository] = None


def get_config_repo(session: Optional[AsyncSession] = None) -> ConfigRepository:
    """ConfigRepo Provider. Eğer session verilirse yeni instance döner (UoW için)."""
    global _config_repo
    if session:
        return ConfigRepository(session=session)
    with _config_repo_lock:
        if _config_repo is None:
            _config_repo = ConfigRepository()
    return _config_repo
