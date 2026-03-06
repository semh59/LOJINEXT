from datetime import datetime, timezone
from typing import Optional

from app.database.repositories.lokasyon_repo import get_lokasyon_repo
from app.infrastructure.events.event_bus import EventType, get_event_bus, publishes
from app.infrastructure.logging.logger import get_logger
from app.schemas.lokasyon import LokasyonCreate, LokasyonResponse, LokasyonUpdate

logger = get_logger(__name__)


class LokasyonService:
    """Lokasyon/Güzergah iş mantığı servisi"""

    def __init__(self, repo=None, event_bus=None):
        self.repo = repo or get_lokasyon_repo()
        self.event_bus = event_bus or get_event_bus()

    @publishes(EventType.LOKASYON_ADDED)
    async def add_lokasyon(self, data: LokasyonCreate) -> int:
        """
        Yeni lokasyon/güzergah ekle.
        """
        # Normalize names to prevent duplicates (e.g., Istanbul vs İstanbul)
        # We store display names as title-cased for UI consistency
        data.cikis_yeri = data.cikis_yeri.strip().title()
        data.varis_yeri = data.varis_yeri.strip().title()

        # We use consistent normalization for checking existing records
        # in the repository (which now handles it in SQL)
        existing = await self.repo.get_by_route(data.cikis_yeri, data.varis_yeri)
        if existing:
            if existing.get("aktif"):
                raise ValueError(
                    f"Bu güzergah zaten mevcut: {data.cikis_yeri} -> {data.varis_yeri}"
                )
            else:
                # Pasif ise geri getir ve güncelle
                logger.info(
                    f"Pasif lokasyon tekrar aktifleştiriliyor: {data.cikis_yeri} -> {data.varis_yeri}"
                )
                await self.repo.update(
                    existing["id"], aktif=True, **data.model_dump(exclude_unset=True)
                )
                return existing["id"]

        lokasyon_id = await self.repo.add(**data.model_dump())
        logger.info(f"Yeni güzergah eklendi: ID {lokasyon_id}")

        # Rota analizi yap (Opsiyonel - eğer koordinatlar varsa veya sadece isimden bulmaya çalışıyorsak)
        # Şimdilik sadece koordinat varsa veya isimlerden bulmaya çalışıyorsak tetikleyebiliriz.
        # create_guzergah mantığını buraya taşıyoruz:
        payload = data.model_dump()
        if all(
            [
                payload.get("cikis_lat"),
                payload.get("cikis_lon"),
                payload.get("varis_lat"),
                payload.get("varis_lon"),
            ]
        ):
            try:
                # Arka planda analiz başlatılabilir veya senkron yapılabilir.
                # create_guzergah senkron yapıyordu, biz de öyle yapalım şimdilik.
                await self.analyze_route(lokasyon_id)
            except Exception as e:
                logger.warning(
                    f"Otomatik rota analizi başarısız (ID: {lokasyon_id}): {e}"
                )

        return lokasyon_id

    @publishes(EventType.LOKASYON_UPDATED)
    async def update_lokasyon(self, lokasyon_id: int, data: LokasyonUpdate) -> bool:
        """Güzergah güncelle"""
        success = await self.repo.update(
            lokasyon_id, **data.model_dump(exclude_unset=True)
        )
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

            if current.get("aktif"):
                # Soft Delete
                success = await self.repo.update(lokasyon_id, aktif=False)
                if success:
                    logger.info(
                        f"Güzergah pasife alındı (Soft Deleted): ID {lokasyon_id}"
                    )
                return success
            else:
                # Hard Delete
                try:
                    success = await self.repo.hard_delete(lokasyon_id)
                    if success:
                        logger.info(
                            f"Güzergah tamamen silindi (Hard Deleted): ID {lokasyon_id}"
                        )
                    return success
                except Exception as e:
                    logger.warning(f"Hard delete engellendi: {e}")
                    raise ValueError(
                        "Bu güzergah silinemez (bağımlı veriler olabilir)."
                    )
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
        search: Optional[str] = None,
    ) -> dict:
        """Sayfalı ve filtreli lokasyon listesi + Toplam Sayı"""
        filters = {}
        if zorluk:
            filters["zorluk"] = zorluk
        if search:
            filters["search"] = search

        # Get records
        records = await self.repo.get_all(
            offset=skip, limit=limit, include_inactive=not aktif_only, filters=filters
        )

        # Get total count (new repo method needed or generic count)
        total = await self.repo.count(filters=filters, include_inactive=not aktif_only)

        items = []
        for r in records:
            try:
                items.append(LokasyonResponse.model_validate(dict(r)))
            except Exception as e:
                logger.error(f"Lokasyon validasyon hatasi (ID {r.get('id')}): {e}")
                continue

        return {"items": items, "total": total}

    async def analyze_route(self, lokasyon_id: int) -> dict:
        """Hibrit RouteService kullanarak güzergahı analiz et ve güncelle"""
        # Centralized logic via RouteService (Hybrid + Validation support)
        from app.services.route_service import get_route_service

        # 1. Lokasyon bilgilerini getir
        loc = await self.repo.get_by_id(lokasyon_id)
        if not loc or not all(
            [
                loc.get("cikis_lat"),
                loc.get("cikis_lon"),
                loc.get("varis_lat"),
                loc.get("varis_lon"),
            ]
        ):
            raise ValueError(f"Lokasyon {lokasyon_id} koordinat bilgileri eksik.")

        # 2. RouteService üzerinden analiz yap (Hybrid: ORS -> Validator -> Mapbox Fallback)
        route_service = get_route_service()
        # RouteService accepts (lon, lat) tuples
        start_coords = (loc["cikis_lon"], loc["cikis_lat"])
        end_coords = (loc["varis_lon"], loc["varis_lat"])

        # use_cache=False because we want fresh analysis/correction
        result = await route_service.get_route_details(
            start_coords, end_coords, use_cache=False
        )

        if "error" in result:
            raise ValueError(f"Analiz hatası: {result['error']}")

        # 3. Sonuçları veritabanına yansıt
        await self.repo.update(
            lokasyon_id,
            mesafe_km=result["distance_km"],
            tahmini_sure_saat=round(result["duration_min"] / 60, 2),
            api_mesafe_km=result["distance_km"],
            api_sure_saat=round(result["duration_min"] / 60, 2),
            ascent_m=result["ascent_m"],
            descent_m=result["descent_m"],
            flat_distance_km=result["flat_distance_km"],
            otoban_mesafe_km=result.get("otoban_mesafe_km"),
            sehir_ici_mesafe_km=result.get("sehir_ici_mesafe_km"),
            zorluk=result.get("difficulty", loc.get("zorluk", "Normal")),
            source=result.get("source"),
            is_corrected=result.get("is_corrected", False),
            correction_reason=result.get("correction_reason"),
            route_analysis=result.get("route_analysis"),
            last_api_call=datetime.now(timezone.utc),
        )

        logger.info(
            f"Güzergah {lokasyon_id} hibrit servis ile güncellendi. Kaynak: {result.get('source')}"
        )
        return result


def get_lokasyon_service() -> LokasyonService:
    from app.core.container import get_container

    return get_container().lokasyon_service
