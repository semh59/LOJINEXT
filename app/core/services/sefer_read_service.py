"""
TIR Yakıt Takip Sistemi - Sefer Okuma Servisi
Command-Query Separation (CQS) prensibi gereği sadece okuma işlemlerini yönetir.
"""

from typing import Any, Dict, List, Optional
from datetime import date

from app.core.entities.models import Sefer
from app.schemas.sefer import SeferResponse
from app.core.services.security_service import SecurityService
from app.database.models import Kullanici
from app.database.repositories.sefer_repo import SeferRepository, get_sefer_repo
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SeferReadService:
    """
    Sefer okuma işlemleri (Read-Only).
    """

    def __init__(self, repo: Optional[SeferRepository] = None):
        self.repo = repo or get_sefer_repo()

    async def get_by_id(
        self, sefer_id: int, current_user: Optional[Kullanici] = None
    ) -> Optional[Sefer]:
        """ID ile sefer getir (İzolasyon korumalı)"""
        row = await self.repo.get_by_id_with_details(sefer_id)
        if not row:
            return None

        sefer = Sefer.model_validate(row)

        # Ownership check
        if current_user:
            SecurityService.verify_ownership(current_user, sefer.sofor_id)

        return sefer

    async def get_sefer_by_id(
        self, sefer_id: int, current_user: Optional[Kullanici] = None
    ) -> Optional[Dict[str, Any]]:
        """Legacy support for Dict return (İzolasyon korumalı)"""
        sefer = await self.get_by_id(sefer_id, current_user)
        return sefer.model_dump() if sefer else None

    async def get_by_vehicle(self, arac_id: int, limit: int = 50) -> List[Sefer]:
        """Araç sefer geçmişini getir"""
        records = await self.repo.get_all(arac_id=arac_id, limit=limit)
        return [Sefer.model_validate(dict(r)) for r in records]

    async def get_all_paged(
        self,
        current_user: Optional[Kullanici] = None,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        **filters: Any,
    ) -> Dict[str, Any]:
        """
        Sayfalı ve filtreli sefer listesi (Güvenli Katman).
        Kullanıcı yetkisine göre veri izolasyonu (Isolation) uygular.
        """
        limit = min(max(1, limit), 5005)
        skip = max(0, skip)

        # Default security guard against synthetic data
        if "is_real" not in filters:
            filters["is_real"] = True

        if current_user:
            filters = SecurityService.apply_isolation(current_user, filters)

        # Total count for metadata
        total = await self.repo.count_all(
            include_inactive=not aktif_only, filters=filters
        )

        records = await self.repo.get_all(
            offset=skip, limit=limit, include_inactive=not aktif_only, filters=filters
        )

        results: List[SeferResponse] = []
        for r in records:
            try:
                # Ensure we handle the dict conversion
                data = dict(r) if not isinstance(r, dict) else r
                results.append(SeferResponse.model_validate(data))
            except Exception as e:
                logger.error(f"Sefer validasyon hatasi (ID {r.get('id')}): {e}")
                continue

        return {
            "items": results,
            "meta": {"total": total, "skip": skip, "limit": limit},
        }

    async def get_all_trips(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sofor_id: Optional[int] = None,
        arac_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Sefer]:
        """Filtreli sefer listesi (Legacy support, redirected to paged)"""
        # Note: This returns List[Sefer], but get_all_paged returns Dict.
        # We need to adapt it.
        paged_result = await self.get_all_paged(
            limit=limit,
            arac_id=arac_id,
            sofor_id=sofor_id,
            baslangic_tarih=start_date,
            bitis_tarih=end_date,
            durum=status,
        )

        # Convert SeferResponse back to Sefer models if needed, or just return SeferResponse list
        # (SeferResponse is usually compatible with Sefer for read purposes)
        return paged_result["items"]
