"""
TIR Yakıt Takip Sistemi - Sefer Servisi (Facade)
Bu sınıf artık bir "God Class" değil, alt servislere yönlendirme yapan bir Facade'dir.
Backward compatibility için tutulmuştur.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from app.core.entities.models import Sefer, SeferCreate, SeferUpdate
from app.database.models import Kullanici
from app.infrastructure.events.event_bus import EventBus, get_event_bus
from app.database.repositories.sefer_repo import SeferRepository, get_sefer_repo
from app.infrastructure.logging.logger import get_logger

# Import Sub-Services
from app.core.services.sefer_read_service import SeferReadService
from app.core.services.sefer_write_service import SeferWriteService
from app.core.services.sefer_analiz_service import SeferAnalizService

logger = get_logger(__name__)


class SeferService:
    """
    Sefer işlemleri için Facade.
    Tüm istekleri ilgili alt servise (Read/Write/Analiz) yönlendirir.
    """

    def __init__(
        self,
        repo: Optional[SeferRepository] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.repo = repo or get_sefer_repo()
        self.event_bus = event_bus or get_event_bus()

        # Initialize Sub-Services
        self.read_service = SeferReadService(repo=self.repo)
        self.write_service = SeferWriteService(repo=self.repo, event_bus=self.event_bus)
        self.analiz_service = SeferAnalizService(
            repo=self.repo, event_bus=self.event_bus
        )

    # --- READ OPERATIONS (Delegated to SeferReadService) ---

    async def get_by_id(
        self, sefer_id: int, current_user: Optional[Kullanici] = None
    ) -> Optional[Sefer]:
        return await self.read_service.get_by_id(sefer_id, current_user)

    async def get_sefer_by_id(
        self, sefer_id: int, current_user: Optional[Kullanici] = None
    ) -> Optional[Dict[str, Any]]:
        return await self.read_service.get_sefer_by_id(sefer_id, current_user)

    async def get_by_vehicle(self, arac_id: int, limit: int = 50) -> List[Sefer]:
        return await self.read_service.get_by_vehicle(arac_id, limit)

    async def get_all_paged(
        self,
        current_user: Optional[Kullanici] = None,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        **filters: Any,
    ) -> Dict[str, Any]:
        return await self.read_service.get_all_paged(
            current_user, skip, limit, aktif_only, **filters
        )

    async def get_all_trips(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sofor_id: Optional[int] = None,
        arac_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Any]:
        return await self.read_service.get_all_trips(
            start_date, end_date, sofor_id, arac_id, status, limit
        )

    async def get_trip_stats(
        self,
        durum: Optional[str] = None,
        baslangic_tarih: Optional[date] = None,
        bitis_tarih: Optional[date] = None,
    ) -> Dict[str, Any]:
        return await self.read_service.get_trip_stats(
            durum=durum,
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
        )

    async def get_fuel_performance_analytics(
        self,
        durum: Optional[str] = None,
        baslangic_tarih: Optional[date] = None,
        bitis_tarih: Optional[date] = None,
        arac_id: Optional[int] = None,
        sofor_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self.read_service.get_fuel_performance_analytics(
            durum=durum,
            baslangic_tarih=baslangic_tarih,
            bitis_tarih=bitis_tarih,
            arac_id=arac_id,
            sofor_id=sofor_id,
            search=search,
        )

    async def get_timeline(self, sefer_id: int) -> List[Dict[str, Any]]:
        return await self.read_service.get_timeline(sefer_id)

    # --- WRITE OPERATIONS (Delegated to SeferWriteService) ---

    async def add_sefer(self, data: SeferCreate, user_id: Optional[int] = None) -> int:
        return await self.write_service.add_sefer(data, user_id)

    async def update_sefer(
        self, sefer_id: int, data: SeferUpdate, user_id: Optional[int] = None
    ) -> bool:
        return await self.write_service.update_sefer(sefer_id, data, user_id)

    async def delete_sefer(self, sefer_id: int) -> bool:
        return await self.write_service.delete_sefer(sefer_id)

    async def bulk_add_sefer(self, sefer_list: List[SeferCreate]) -> int:
        return await self.write_service.bulk_add_sefer(sefer_list)

    async def create_return_trip(
        self, sefer_id: int, user_id: Optional[int] = None
    ) -> int:
        return await self.write_service.create_return_trip(sefer_id, user_id)

    async def bulk_update_status(
        self, sefer_ids: List[int], new_status: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        return await self.write_service.bulk_update_status(
            sefer_ids, new_status, user_id
        )

    async def bulk_cancel(
        self, sefer_ids: List[int], iptal_nedeni: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        return await self.write_service.bulk_cancel(sefer_ids, iptal_nedeni, user_id)

    async def bulk_delete(self, sefer_ids: List[int]) -> Dict[str, Any]:
        return await self.write_service.bulk_delete(sefer_ids)

    # --- ANALYSIS OPERATIONS (Delegated to SeferAnalizService) ---

    async def reconcile_costs(self, sefer_id: int) -> Dict[str, Any]:
        return await self.analiz_service.reconcile_costs(sefer_id)


def get_sefer_service() -> SeferService:
    """Dependency Injection provider"""
    from app.core.container import get_container

    return get_container().sefer_service
