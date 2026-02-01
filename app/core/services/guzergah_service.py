"""
Güzergah (Route) Servisi
İş mantığı katmanı: Güzergah işlemleri
"""

from typing import List, Optional
from app.core.entities.models import Guzergah
from app.database.repositories.guzergah_repo import get_guzergah_repo
from app.schemas.guzergah import GuzergahCreate, GuzergahUpdate
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class GuzergahService:
    def __init__(self, repo=None):
        self.repo = repo or get_guzergah_repo()

    async def get_all_active(self) -> List[Guzergah]:
        """Aktif güzergahları getir"""
        return await self.repo.get_all_active()

    async def get_by_id(self, id: int) -> Optional[Guzergah]:
        """ID ile güzergah getir"""
        return await self.repo.get_by_id(id)

    async def create_guzergah(self, data: GuzergahCreate) -> Guzergah:
        """Yeni güzergah oluştur"""
        # Burada ad çakışması kontrolü yapılabilir
        return await self.repo.create_guzergah(data.model_dump())

    async def update_guzergah(self, id: int, data: GuzergahUpdate) -> bool:
        """Güzergah güncelle"""
        return await self.repo.update_guzergah(id, data.model_dump(exclude_unset=True))

    async def delete_guzergah(self, id: int) -> bool:
        """Güzergah sil (Soft delete - aktif=False)"""
        return await self.repo.soft_delete(id)


# Singleton
import threading
_guzergah_service_lock = threading.Lock()
_guzergah_service: Optional[GuzergahService] = None

def get_guzergah_service() -> GuzergahService:
    global _guzergah_service
    with _guzergah_service_lock:
        if _guzergah_service is None:
            _guzergah_service = GuzergahService()
    return _guzergah_service
