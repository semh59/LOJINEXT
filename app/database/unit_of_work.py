"""
LojiNext AI - Unit of Work Pattern
Birden fazla repository işlemini tek bir transaction altında toplar.
"""

from typing import Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import AsyncSessionLocal
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class UnitOfWork:
    """
    Unit of Work (UoW) Pattern implementation.
    Repository'ler arası veri tutarlılığını ve atomik işlemleri garanti eder.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session: Optional[AsyncSession] = session
        self._external_session = session is not None
        self._committed = False
        self._rolled_back = False
        self._yakit_repo = None
        self._sefer_repo = None
        self._arac_repo = None
        self._sofor_repo = None
        self._analiz_repo = None
        self._lokasyon_repo = None
        self._config_repo = None
        self._kullanici_repo = None
        self._route_repo = None
        self._session_repo = None
        self._audit_repo = None
        self._admin_config_repo = None
        self._ml_training_repo = None
        self._model_versiyon_repo = None
        self._import_repo = None
        self._maintenance_repo = None
        self._notification_repo = None
        self._dorse_repo = None
        self._setting_repo = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError(
                "UnitOfWork session not initialized. Use 'async with uow:'"
            )
        return self._session

    async def __aenter__(self):
        if self._session is None:
            self._session = AsyncSessionLocal()
            self._external_session = False
            logger.debug(f"[UOW] Created session {id(self._session)}")
        # Add tracing
        self.session.info["uow_active"] = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                logger.warning(f"UoW error detected, triggering rollback: {exc_val}")
                await self.rollback()
            elif (
                not self._external_session
                and not self._committed
                and not self._rolled_back
                and self._session
            ):
                if self._session.new or self._session.dirty or self._session.deleted:
                    logger.error(
                        "GHOST TRANSACTION: UoW block exited with pending changes but without explicit commit or rollback. Safety rollback triggered."
                    )
                    await self.rollback()
        except Exception as e:
            logger.error(f"Error during UoW exit: {e}", exc_info=True)
            raise
        finally:
            if not self._external_session and self._session:
                await self._session.close()
                self._session = None
            elif self._session:
                self._session.info["uow_active"] = False

    @property
    def info(self) -> dict:
        """Oturumun info sözlü■ünü döndürür."""
        return self._session.info if self._session else {}

    async def flush(self):
        """Mevcut oturumu flush et (ID'leri olu■turur ama commit etmez)."""
        await self._session.flush()

    async def commit(self):
        if self._session:
            try:
                await self._session.commit()
                self._committed = True
            except Exception as e:
                logger.error(f"Commit failed: {e}", exc_info=True)
                await self.rollback()
                raise

    async def rollback(self):
        if self._session:
            try:
                await self._session.rollback()
            except Exception as e:
                # Log but verify we don't crash the rollback process itself
                logger.error(f"Rollback failed: {e}", exc_info=True)
            finally:
                self._rolled_back = True

    @property
    def event_bus(self):
        """EventBus instance."""
        from app.infrastructure.events.event_bus import get_event_bus

        return get_event_bus()

    @property
    def kullanici_repo(self):
        if self._kullanici_repo is None:
            from app.database.repositories.kullanici_repo import KullaniciRepository

            self._kullanici_repo = KullaniciRepository(session=self.session)
        return self._kullanici_repo

    @property
    def session_repo(self):
        if self._session_repo is None:
            from app.database.repositories.session_repo import SessionRepository

            self._session_repo = SessionRepository(session=self.session)
        return self._session_repo

    @property
    def audit_repo(self):
        if self._audit_repo is None:
            from app.database.repositories.audit_repo import AuditRepository

            self._audit_repo = AuditRepository(session=self.session)
        return self._audit_repo

    @property
    def admin_config_repo(self):
        if self._admin_config_repo is None:
            from app.database.repositories.admin_config_repo import (
                AdminConfigRepository,
            )

            self._admin_config_repo = AdminConfigRepository(session=self.session)
        return self._admin_config_repo

    @property
    def ml_training_repo(self):
        if self._ml_training_repo is None:
            from app.database.repositories.ml_training_repo import MLTrainingRepository

            self._ml_training_repo = MLTrainingRepository(session=self.session)
        return self._ml_training_repo

    @property
    def model_versiyon_repo(self):
        if self._model_versiyon_repo is None:
            from app.database.repositories.ml_training_repo import (
                ModelVersiyonRepository,
            )

            self._model_versiyon_repo = ModelVersiyonRepository(session=self.session)
        return self._model_versiyon_repo

    @property
    def import_repo(self):
        if self._import_repo is None:
            from app.database.repositories.import_repo import ImportHistoryRepository

            self._import_repo = ImportHistoryRepository(session=self.session)
        return self._import_repo

    @property
    def analiz_repo(self):
        if self._analiz_repo is None:
            from app.database.repositories.analiz_repo import AnalizRepository

            self._analiz_repo = AnalizRepository(session=self.session)
        return self._analiz_repo

    @property
    def config_repo(self):
        if self._config_repo is None:
            from app.database.repositories.config_repo import ConfigRepository

            self._config_repo = ConfigRepository(session=self.session)
        return self._config_repo

    @property
    def route_repo(self):
        if self._route_repo is None:
            from app.database.repositories.route_repo import RouteRepository

            self._route_repo = RouteRepository(session=self.session)
        return self._route_repo

    # Legacy properties kept for compatibility
    @property
    def yakit_repo(self):
        if self._yakit_repo is None:
            from app.database.repositories.yakit_repo import YakitRepository

            self._yakit_repo = YakitRepository(session=self.session)
        return self._yakit_repo

    @property
    def sefer_repo(self):
        if self._sefer_repo is None:
            from app.database.repositories.sefer_repo import SeferRepository

            self._sefer_repo = SeferRepository(session=self.session)
        return self._sefer_repo

    @property
    def lokasyon_repo(self):
        if self._lokasyon_repo is None:
            from app.database.repositories.lokasyon_repo import LokasyonRepository

            self._lokasyon_repo = LokasyonRepository(session=self.session)
        return self._lokasyon_repo

    @property
    def arac_repo(self):
        if self._arac_repo is None:
            from app.database.repositories.arac_repo import AracRepository

            self._arac_repo = AracRepository(session=self.session)
        return self._arac_repo

    @property
    def sofor_repo(self):
        if self._sofor_repo is None:
            from app.database.repositories.sofor_repo import SoforRepository

            self._sofor_repo = SoforRepository(session=self.session)
        return self._sofor_repo

    @property
    def maintenance_repo(self):
        if self._maintenance_repo is None:
            from app.database.repositories.maintenance_repository import (
                MaintenanceRepository,
            )

            self._maintenance_repo = MaintenanceRepository(session=self.session)
        return self._maintenance_repo

    @property
    def notification_repo(self):
        if self._notification_repo is None:
            from app.database.repositories.notification_repository import (
                NotificationRepository,
            )

            self._notification_repo = NotificationRepository(session=self.session)
        return self._notification_repo

    @property
    def dorse_repo(self):
        if self._dorse_repo is None:
            from app.database.repositories.dorse_repo import DorseRepository

            self._dorse_repo = DorseRepository(session=self.session)
        return self._dorse_repo

    @property
    def setting_repo(self):
        if self._setting_repo is None:
            from app.database.repositories.setting_repository import SettingRepository

            self._setting_repo = SettingRepository(session=self.session)
        return self._setting_repo


async def get_uow():
    """Unit of Work Context Manager Provider (FastAPI Dependency)"""
    async with UnitOfWork() as uow:
        yield uow
