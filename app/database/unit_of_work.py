"""
LojiNext AI - Unit of Work Pattern
Birden fazla repository işlemini tek bir transaction altında toplar.
"""

from contextlib import contextmanager
from typing import Optional, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import AsyncSessionLocal
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

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

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork session not initialized. Use 'async with uow:'")
        return self._session

    async def __aenter__(self):
        if self._session is None:
            self._session = AsyncSessionLocal()
            self._external_session = False
        # Add tracing
        self.session.info["uow_active"] = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                logger.warning(f"UoW error detected, triggering rollback: {exc_val}")
                await self.rollback()
            elif not self._external_session and not self._committed and not self._rolled_back:
                # GHOST TRANSACTION DETECTION:
                # If we are exiting without commit/rollback and it's NOT an external session,
                # we must log it and rollback for safety.
                logger.error("GHOST TRANSACTION: UoW block exited without explicit commit or rollback. Safety rollback triggered.")
                await self.rollback()
        except Exception as e:
            logger.error(f"Error during UoW exit: {e}", exc_info=True)
            raise
        finally:
            if not self._external_session and self._session:
                # Ensure session is closed
                await self._session.close()
                self._session = None
            elif self._session:
                # Even for external sessions, we mark UoW as inactive in the session info
                self._session.info["uow_active"] = False

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

    @contextmanager
    def nested(self):
        """
        Creates a savepoint for nested transactions.
        Usage:
            async with uow:
                with uow.nested():
                    ...
        """
        if not self._session:
            raise RuntimeError("UoW session not active")
            
        nested_tx = self._session.begin_nested()
        try:
            yield nested_tx
        except:
            # begin_nested() automatically rolls back on exception when used as context manager
            # but we explicitly log it here if needed
            raise


    # Lazily initialized repositories with shared session
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
    def analiz_repo(self):
        if self._analiz_repo is None:
            from app.database.repositories.analiz_repo import AnalizRepository
            self._analiz_repo = AnalizRepository(session=self.session)
        return self._analiz_repo

    @property
    def lokasyon_repo(self):
        if self._lokasyon_repo is None:
            from app.database.repositories.lokasyon_repo import LokasyonRepository
            self._lokasyon_repo = LokasyonRepository(session=self.session)
        return self._lokasyon_repo

    @property
    def config_repo(self):
        if self._config_repo is None:
            from app.database.repositories.config_repo import ConfigRepository
            self._config_repo = ConfigRepository(session=self.session)
        return self._config_repo

    @property
    def kullanici_repo(self):
        if self._kullanici_repo is None:
            from app.database.repositories.kullanici_repo import KullaniciRepository
            self._kullanici_repo = KullaniciRepository(session=self.session)
        return self._kullanici_repo

    @property
    def route_repo(self):
        if self._route_repo is None:
            from app.database.repositories.route_repo import RouteRepository
            self._route_repo = RouteRepository(session=self.session)
        return self._route_repo

def get_uow() -> UnitOfWork:
    """UoW Provider"""
    return UnitOfWork()
