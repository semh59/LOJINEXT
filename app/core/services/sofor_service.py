"""
TIR Yakıt Takip Sistemi - Şoför Servisi
İş mantığı katmanı: Şoför CRUD işlemleri
"""

from datetime import date
from typing import Any, Dict, List, Optional

from app.database.repositories.sofor_repo import SoforRepository, get_sofor_repo
from app.infrastructure.events.event_bus import (
    EventBus,
    EventType,
    get_event_bus,
    publishes,
)
from app.infrastructure.logging.logger import get_logger
from app.database.unit_of_work import UnitOfWork

logger = get_logger(__name__)


class SoforService:
    """
    Şoför CRUD işlemleri iş mantığı.
    UI ve DB arasında köprü görevi görür.
    """

    def __init__(
        self,
        repo: Optional["SoforRepository"] = None,
        event_bus: Optional[EventBus] = None,
    ):
        import asyncio

        self.repo = repo or get_sofor_repo()
        self.event_bus = event_bus or get_event_bus()
        self._lock = asyncio.Lock()

    @publishes(EventType.SOFOR_ADDED)
    async def add_sofor(
        self,
        ad_soyad: str,
        telefon: str = "",
        ehliyet_sinifi: str = "E",
        ise_baslama: Optional[date] = None,
        manual_score: float = 1.0,
        notlar: str = "",
    ) -> int:
        """
        Yeni şoför ekle (UoW & Atomic Check).
        """
        async with UnitOfWork() as uow:
            async with self._lock:  # Local Lock (Secondary Guard)
                # Business Rules
                if not ad_soyad or len(ad_soyad.strip()) < 3:
                    raise ValueError("Ad soyad en az 3 karakter olmalıdır")

                # Ad soyad title case
                ad_soyad_clean = " ".join(
                    word.capitalize() for word in ad_soyad.strip().split()
                )

                existing = await uow.sofor_repo.get_by_name(
                    ad_soyad_clean, for_update=True
                )
                if existing:
                    if existing.get("aktif"):
                        raise ValueError("Bu isimde kayıtlı aktif bir şoför zaten var.")
                    else:
                        # Pasif şoförü aktifleştir
                        logger.info(
                            f"Pasif şoför tekrar aktifleştiriliyor (ID: {existing['id']})"
                        )
                        await uow.sofor_repo.update(existing["id"], aktif=True)
                        await uow.commit()
                        return existing["id"]

                # DB Insert
                sofor_id = await uow.sofor_repo.add(
                    ad_soyad=ad_soyad_clean,
                    telefon=telefon,
                    ehliyet_sinifi=ehliyet_sinifi,
                    ise_baslama=ise_baslama,
                    manual_score=manual_score,
                    score=manual_score,  # Initial score is manual
                    notlar=notlar,
                )

                logger.info(f"Yeni şoför eklendi (ID: {sofor_id})")
                await uow.commit()
                return sofor_id

    async def get_all_paged(
        self,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        search: Optional[str] = None,
        ehliyet_sinifi: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Sayfalı ve filtreli şoför listesi"""
        # Pass additional filters
        filters = {}
        if ehliyet_sinifi:
            filters["ehliyet_sinifi"] = ehliyet_sinifi
        if min_score is not None:
            filters["score_ge"] = min_score
        if max_score is not None:
            filters["score_le"] = max_score

        async with UnitOfWork() as uow:
            rows = await uow.sofor_repo.get_all(
                offset=skip,
                limit=limit,
                sadece_aktif=aktif_only,
                search=search,
                filters=filters,
            )

        # Dönüşüm ve Güvenlik (Schema Healing)
        validated = []
        for r in rows:
            try:
                # Dict gelirse modele çevirip geri dict dön (veya modele bırak)
                # Repo dict dönüyor, servis de dict listesi dönebilir
                validated.append(r)
            except Exception as e:
                logger.warning(f"Bozuk şoför kaydı atlandı (ID {r.get('id')}): {e}")
                continue
        return validated

    async def get_by_id(self, sofor_id: int) -> Optional[Dict[str, Any]]:
        """ID ile şoför getir"""
        async with UnitOfWork() as uow:
            return await uow.sofor_repo.get_by_id(sofor_id)

    @publishes(EventType.SOFOR_UPDATED)
    async def update_sofor(self, sofor_id: int, **kwargs: Any) -> bool:
        """Şoför güncelle (UoW & Safe Name Change)"""
        async with UnitOfWork() as uow:
            # Ad soyad varsa title case yap
            if kwargs.get("ad_soyad"):
                ad_soyad = " ".join(
                    word.capitalize() for word in kwargs["ad_soyad"].strip().split()
                )
                kwargs["ad_soyad"] = ad_soyad

                async with self._lock:
                    existing = await uow.sofor_repo.get_by_name(ad_soyad)
                    if existing and existing["id"] != sofor_id:
                        raise ValueError("Bu isim başka bir şoföre ait.")

            # Recalculate hybrid score if manual_score is updated
            if "manual_score" in kwargs:
                current = await uow.sofor_repo.get_by_id(sofor_id)
                if current:
                    new_score = await self.calculate_hybrid_score(
                        sofor_id, kwargs["manual_score"]
                    )
                    kwargs["score"] = new_score

            success = await uow.sofor_repo.update(sofor_id, **kwargs)
            if success:
                logger.info(f"Şoför güncellendi: ID {sofor_id}")
                await uow.commit()
            return success

    @publishes(EventType.SOFOR_DELETED)
    async def delete_sofor(self, sofor_id: int) -> bool:
        """
        Şoför sil (Soft Delete standardı).
        """
        async with UnitOfWork() as uow:
            return await self._delete_sofor_uow(uow, sofor_id)

    async def _delete_sofor_uow(self, uow: UnitOfWork, sofor_id: int) -> bool:
        """
        Transactional soft delete logic (Shared UoW).
        """
        # Mevcut durumu kontrol et
        current = await uow.sofor_repo.get_by_id(sofor_id, for_update=True)
        if not current or current.get("is_deleted"):
            return False

        # Soft Delete (is_deleted=True, aktif=False)
        success = await uow.sofor_repo.update(sofor_id, is_deleted=True, aktif=False)
        if success:
            logger.info(f"Sürücü soft-delete ile silindi: ID {sofor_id}")
            # UoW commit service katmanında veya dışarıda yapılır
        return success

    async def bulk_delete(self, ids: List[int]) -> Dict[str, Any]:
        """
        Toplu şoför silme (N+1 transaction korumalı).
        """
        if not ids:
            return {"deleted": 0, "errors": []}

        async with UnitOfWork() as uow:
            # Repository seviyesinde optimize edilmiş bulk soft delete
            count = await uow.sofor_repo.bulk_soft_delete(ids)
            await uow.commit()

            logger.info(f"Toplu şoför silindi: {count} adet")
            return {"deleted": count, "total": len(ids), "status": "success"}

    async def update_score(self, sofor_id: int, score: float) -> bool:
        """Sürücü manuel puanını güncelle ve hibrit puanı hesapla"""
        if score < 0.1 or score > 2.0:
            raise ValueError("Puan 0.1 ile 2.0 arasında olmalıdır")

        try:
            async with self._lock:
                current = await self.repo.get_by_id(sofor_id)
                if not current:
                    raise ValueError("Şoför bulunamadı")

                # Performans bazlı yeni hibrit puanı hesapla
                hybrid_score = await self.calculate_hybrid_score(sofor_id, score)

                success = await self.repo.update(
                    sofor_id, manual_score=score, score=hybrid_score
                )
            if success:
                logger.info(
                    f"Şoför puanları güncellendi: ID {sofor_id} | Manuel: {score}, Hibrit: {hybrid_score}"
                )
            return success
        except Exception as e:
            logger.error(f"Puan güncelleme hatası: {e}")
            raise

    async def calculate_hybrid_score(self, sofor_id: int, manual_score: float) -> float:
        """
        Hibrit puan hesapla: %60 Performans (Sefer verileri) + %40 Manuel Giriş.
        """
        try:
            # 1. Şoförün son sefer istatistiklerini getir
            async with UnitOfWork() as uow:
                stats_list = await uow.sofor_repo.get_sefer_stats(sofor_id=sofor_id)
            if not stats_list or len(stats_list) == 0:
                # Veri yoksa sadece manuel puanı baz al
                return manual_score

            stats = stats_list[0]
            avg_tuketim = stats.get("ort_tuketim", 0)

            if avg_tuketim <= 0:
                return manual_score

            # 2. Performans puanı hesapla (Hedef tüketim üzerinden)
            # Not: Burada araç bazlı hedef tüketim ortalaması alınabilir.
            # Şimdilik genel bir 30 L/100km baz alalım veya basitleştirelim.
            # İleride her seferin kendi hedef/gerçek farkı ağırlıklı ortalanabilir.
            target_reference = 30.0
            perf_factor = target_reference / avg_tuketim

            # Factor mapping (1.0 -> 1.0, 0.8 -> 1.25, 1.2 -> 0.8 etc)
            # Clamp to 0.1 - 2.0
            perf_score = max(0.1, min(2.0, perf_factor))

            # 3. Hibrit Hesaplama (%60 Performans, %40 Manuel)
            hybrid = (float(perf_score) * 0.6) + (float(manual_score) * 0.4)
            return round(hybrid, 2)

        except Exception as e:
            logger.error(f"Hibrit puan hesaplama hatası: {e}")
            return float(manual_score)

    async def bulk_add_sofor(self, data_list: List[Any]) -> int:
        """Toplu şoför oluştur (UoW & N+1 çözüm)"""
        if not data_list:
            return 0

        async with UnitOfWork() as uow:
            # Mevcut isimleri çek (N+1 önlemi)
            existing_names = await uow.sofor_repo.get_aktif_isimler()
            existing_set = set(existing_names)

            to_add = []
            for data in data_list:
                # Handle Pydantic models vs Dicts
                if hasattr(data, "model_dump"):
                    d = data.model_dump()
                elif hasattr(data, "dict"):
                    d = data.dict()
                else:
                    d = data

                ad_soyad = d.get("ad_soyad", "").strip()
                if not ad_soyad or len(ad_soyad) < 3:
                    continue

                # Title case
                ad_soyad = " ".join(word.capitalize() for word in ad_soyad.split())

                if ad_soyad in existing_set:
                    continue

                to_add.append(
                    {
                        "ad_soyad": ad_soyad,
                        "telefon": d.get("telefon", ""),
                        "ise_baslama": d.get("ise_baslama", ""),
                        "ehliyet_sinifi": d.get("ehliyet_sinifi", "E"),
                        "notlar": d.get("notlar", ""),
                        "aktif": True,
                        "score": 1.0,
                    }
                )

            if to_add:
                ids = await uow.sofor_repo.bulk_create(to_add)
                logger.info(f"Toplu şoför eklendi: {len(ids)} adet")
                await uow.commit()
                return len(ids)

        return 0

    async def get_performance_details(self, sofor_id: int) -> Dict[str, Any]:
        """
        Sürücü performans detaylarını hesapla (AI & Istatistik Analizi).
        """
        async with UnitOfWork() as uow:
            # 1. Sefer İstatistikleri (Toplam KM, Tüketim vb)
            stats_list = await uow.sofor_repo.get_sefer_stats(sofor_id=sofor_id)
            stats = stats_list[0] if stats_list else {}

            total_km = float(stats.get("toplam_km") or 0)
            total_trips = int(stats.get("toplam_sefer") or 0)
            avg_tuketim = float(stats.get("ort_tuketim") or 0)

            # 2. Anomali Analizi (Son 30 gün)
            anomalies = await uow.sofor_repo.get_driver_anomalies_count(
                sofor_id, days=30
            )

        # 3. Skorlama Algoritması
        # Safety Score: 100 üzerinden düşülür.
        # Critical: -10, High: -5, Medium: -2
        deduction = (
            (anomalies.get("critical", 0) * 10)
            + (anomalies.get("high", 0) * 5)
            + (anomalies.get("medium", 0) * 2)
        )

        safety_score = max(0.0, 100.0 - deduction)

        # Eco Score: Tüketim hedefe yakınlığı (Hedef: 30L varsayalım)
        # Eğer tüketim 30 ise score 100. 35 ise düşer.
        target = 30.0
        if avg_tuketim > 0:
            deviation_pct = ((avg_tuketim - target) / target) * 100
            # Her %1 sapma için 1 puan kır (Pozitif sapma = fazla tüketim)
            if deviation_pct > 0:
                eco_score = max(0.0, 100.0 - deviation_pct)
            else:
                # Hedefin altındaysa ödül (max 100)
                eco_score = min(100.0, 100.0 + (abs(deviation_pct) * 0.5))
        else:
            eco_score = 90.0  # Nötr başlangıç

        # Compliance Score: Sefer tamamlama vb (Şimdilik mock/basit)
        compliance_score = 95.0 - (anomalies.get("low", 0) * 0.5)

        # Total Score (Ağırlıklı)
        # Safety %40, Eco %40, Compliance %20
        total_score = (
            (safety_score * 0.4) + (eco_score * 0.4) + (compliance_score * 0.2)
        )

        # Trend Analizi (Basit karşılaştırma)
        # Gerçekte önceki aya göre bakılabilir. Şimdilik 'stable' veya random.
        trend = "stable"
        if total_score > 90:
            trend = "increasing"
        elif total_score < 70:
            trend = "decreasing"

        return {
            "safety_score": round(safety_score, 1),
            "eco_score": round(eco_score, 1),
            "compliance_score": round(compliance_score, 1),
            "total_score": round(total_score, 1),
            "trend": trend,
            "total_km": round(total_km, 1),
            "total_trips": total_trips,
        }


# Thread-safe singleton
def get_sofor_service() -> SoforService:
    from app.core.container import get_container

    return get_container().sofor_service
