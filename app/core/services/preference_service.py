from typing import List, Optional, Any
from app.database.unit_of_work import UnitOfWork
from app.database.models import KullaniciAyari
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class PreferenceService:
    """Service for managing user-specific preferences (saved filters, columns, etc)."""

    async def get_preferences(
        self, user_id: int, modul: str, ayar_tipi: Optional[str] = None
    ) -> List[KullaniciAyari]:
        """Fetch preferences for a user and module."""
        async with UnitOfWork() as uow:
            return await uow.setting_repo.get_user_settings(user_id, modul, ayar_tipi)

    async def save_preference(
        self,
        user_id: int,
        modul: str,
        ayar_tipi: str,
        deger: Any,
        ad: Optional[str] = None,
        is_default: bool = False,
    ) -> KullaniciAyari:
        """Save or update a user preference."""
        async with UnitOfWork() as uow:
            if is_default:
                # Clear existing default for this module/type
                await uow.setting_repo.clear_default(user_id, modul, ayar_tipi)

            # If it's a 'sutun' (column) type, we usually only have one per module/user
            # We can treat it as an upsert if no 'ad' is provided
            existing = None
            if ayar_tipi == "sutun":
                settings = await uow.setting_repo.get_user_settings(
                    user_id, modul, ayar_tipi
                )
                if settings:
                    existing = settings[0]

            if existing:
                success = await uow.setting_repo.update(
                    existing.id, deger=deger, is_default=is_default
                )
                if success:
                    await uow.commit()
                    return await uow.setting_repo.get_by_id(existing.id)

            # Create new preference
            pref = KullaniciAyari(
                kullanici_id=user_id,
                modul=modul,
                ayar_tipi=ayar_tipi,
                deger=deger,
                ad=ad,
                is_default=is_default,
            )
            await uow.setting_repo.add(pref)
            await uow.commit()
            return pref

    async def delete_preference(self, user_id: int, pref_id: int) -> bool:
        """Delete a user preference."""
        async with UnitOfWork() as uow:
            pref = await uow.setting_repo.get_by_id(pref_id)
            if not pref or pref.kullanici_id != user_id:
                return False

            success = await uow.setting_repo.delete(pref_id)
            if success:
                await uow.commit()
            return success

    async def set_default(self, user_id: int, pref_id: int) -> bool:
        """Set a specific preference as the default."""
        async with UnitOfWork() as uow:
            pref = await uow.setting_repo.get_by_id(pref_id)
            if not pref or pref.kullanici_id != user_id:
                return False

            await uow.setting_repo.clear_default(user_id, pref.modul, pref.ayar_tipi)
            success = await uow.setting_repo.update(pref_id, is_default=True)
            if success:
                await uow.commit()
            return success
