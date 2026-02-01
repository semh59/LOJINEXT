from typing import List, Optional
from datetime import datetime

from app.schemas.lokasyon import LokasyonCreate, LokasyonUpdate, LokasyonResponse
from app.database.repositories.lokasyon_repo import get_lokasyon_repo
from app.infrastructure.events.event_bus import EventType, get_event_bus, publishes
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class LokasyonService:
    """Lokasyon/Güzergah iş mantığı servisi"""

    def __init__(self, repo=None, event_bus=None):
        self.repo = repo or get_lokasyon_repo()
        self.event_bus = event_bus or get_event_bus()

    @publishes(EventType.LOKASYON_ADDED)
    async def add_lokasyon(self, data: LokasyonCreate) -> int:
        """Yeni güzergah oluştur (Duplicate Check)"""
        existing = await self.repo.get_by_route(data.cikis_yeri, data.varis_yeri)
        if existing:
            if existing.get('aktif'):
                raise ValueError(f"Bu güzergah zaten mevcut: {data.cikis_yeri} -> {data.varis_yeri}")
            else:
                # Pasif ise geri getir ve güncelle
                logger.info(f"Pasif lokasyon tekrar aktifleştiriliyor: {data.cikis_yeri} -> {data.varis_yeri}")
                await self.repo.update(
                    existing['id'],
                    aktif=True,
                    **data.model_dump(exclude_unset=True)
                )
                return existing['id']

        lokasyon_id = await self.repo.add(
            **data.model_dump()
        )
        logger.info(f"Yeni güzergah eklendi: ID {lokasyon_id}")
        return lokasyon_id

    @publishes(EventType.LOKASYON_UPDATED)
    async def update_lokasyon(self, lokasyon_id: int, data: LokasyonUpdate) -> bool:
        """Güzergah güncelle"""
        success = await self.repo.update(lokasyon_id, **data.model_dump(exclude_unset=True))
        if success:
            logger.info(f"Güzergah güncellendi: ID {lokasyon_id}")
        return success

    @publishes(EventType.LOKASYON_DELETED)
    async def delete_lokasyon(self, lokasyon_id: int) -> bool:
        """Güzergah sil (Smart Delete: Aktif->Pasif, Pasif->Hard)"""
        try:
            current = await self.repo.get_by_id(lokasyon_id)
            if not current:
                return False

            if current.get('aktif'):
                # Soft Delete
                success = await self.repo.update(lokasyon_id, aktif=False)
                if success:
                    logger.info(f"Güzergah pasife alındı (Soft Deleted): ID {lokasyon_id}")
                return success
            else:
                # Hard Delete
                try:
                    success = await self.repo.hard_delete(lokasyon_id)
                    if success:
                        logger.info(f"Güzergah tamamen silindi (Hard Deleted): ID {lokasyon_id}")
                    return success
                except Exception as e:
                    logger.warning(f"Hard delete engellendi: {e}")
                    raise ValueError("Bu güzergah silinemez (bağımlı veriler olabilir).")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Lokasyon silme hatasi: {e}")
            raise ValueError("Silme işlemi sırasında bir hata oluştu.")

    async def get_all_paged(
        self,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        zorluk: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[LokasyonResponse]:
        """Sayfalı ve filtreli lokasyon listesi (Güvenli Katman)"""
        # Note: LokasyonRepo.get_all doesn't support filters yet in this version, 
        # but BaseRepository.get_all does. LokasyonRepo.get_all just passes order_by.
        # We'll use BaseRepo power via filters dict.
        
        filters = {}
        if zorluk:
            filters['zorluk'] = zorluk
        if search:
            filters['search'] = search

        records = await self.repo.get_all(
            offset=skip,
            limit=limit,
            include_inactive=not aktif_only,
            filters=filters
        )
        
        results = []
        for r in records:
            try:
                results.append(LokasyonResponse.model_validate(dict(r)))
            except Exception as e:
                logger.error(f"Lokasyon validasyon hatasi (ID {r.get('id')}): {e}")
                continue
        return results

    async def analyze_route(self, lokasyon_id: int) -> dict:
        """OpenRouteService kullanarak güzergahı analiz et ve güncelle"""
        current = await self.repo.get_by_id(lokasyon_id)
        if not current:
            raise ValueError("Güzergah bulunamadı")

        if not all([current.get('cikis_lat'), current.get('cikis_lon'), current.get('varis_lat'), current.get('varis_lon')]):
            raise ValueError("Analiz için koordinatlar gerekli.")

        from app.services.route_service import RouteService
        import asyncio

        service = RouteService()
        result = await asyncio.to_thread(
            service.get_route_details,
            (current['cikis_lon'], current['cikis_lat']),
            (current['varis_lon'], current['varis_lat'])
        )

        if "error" in result:
            raise ValueError(f"API Hatası: {result['error']}")

        # Update data
        update_data = {
            "api_mesafe_km": result.get("distance_km"),
            "api_sure_saat": result.get("duration_min", 0) / 60,
            "ascent_m": result.get("ascent_m"),
            "descent_m": result.get("descent_m"),
            "last_api_call": datetime.now(),
            "zorluk": service.analyze_route_difficulty(
                result.get("ascent_m", 0),
                result.get("descent_m", 0),
                result.get("distance_km", 0)
            )
        }

        await self.repo.update(lokasyon_id, **update_data)
        logger.info(f"Güzergah analiz edildi ve güncellendi: ID {lokasyon_id}")
        
        # Extract elevation profile for frontend chart
        geometry = result.get("geometry", {})
        coords = geometry.get("coordinates", [])
        
        elevation_profile = []
        total_dist_m = 0.0
        
        def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
            import math
            R = 6371000
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlamb = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlamb / 2) ** 2
            return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if coords:
            # First point
            elevation_profile.append({
                "distance_km": 0.0,
                "elevation_m": round(coords[0][2], 1) if len(coords[0]) > 2 else 0.0
            })
            
            # Sampling logic: If many points, take every Nth point to avoid large payload
            # or just take all for high resolution
            for i in range(1, len(coords)):
                p1 = coords[i - 1]
                p2 = coords[i]
                d = haversine(p1[0], p1[1], p2[0], p2[1])
                total_dist_m += d
                
                # Sample every ~1km or just use all if route is short
                if i % 10 == 0 or i == len(coords) - 1:
                    elevation_profile.append({
                        "distance_km": round(total_dist_m / 1000, 2),
                        "elevation_m": round(p2[2], 1) if len(p2) > 2 else 0.0
                    })

        result["elevation_profile"] = elevation_profile
        
        # Return merged or just success
        return result

def get_lokasyon_service() -> LokasyonService:
    from app.core.container import get_container
    return get_container().lokasyon_service
