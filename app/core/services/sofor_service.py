"""
TIR Yakıt Takip Sistemi - Şoför Servisi
İş mantığı katmanı: Şoför CRUD işlemleri
"""

from typing import Dict, List, Optional

from app.database.repositories.sofor_repo import get_sofor_repo
from app.infrastructure.events.event_bus import EventType, get_event_bus, publishes
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class SoforService:
    """
    Şoför CRUD işlemleri iş mantığı.
    UI ve DB arasında köprü görevi görür.
    """

    def __init__(self, repo=None, event_bus=None):
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
        ise_baslama: str = None,
        manual_score: float = 1.0,
        notlar: str = ""
    ) -> int:
        """
        Yeni şoför ekle (Atomic Check).
        """
        async with self._lock:  # Race Condition Guard
            try:
                # Business Rules
                if not ad_soyad or len(ad_soyad.strip()) < 3:
                    raise ValueError("Ad soyad en az 3 karakter olmalıdır")

                # Ad soyad title case
                ad_soyad = ' '.join(word.capitalize() for word in ad_soyad.strip().split())

                # Duplicate kontrolü (Optimize: All yerine Tekil Sorgu)
                existing = await self.repo.get_by_name(ad_soyad)
                if existing:
                    if existing.get('aktif'):
                        raise ValueError(f"Bu isimde kayıtlı şoför zaten var: {ad_soyad}")
                    else:
                        # Pasif şoförü aktifleştir
                        logger.info(f"Pasif şoför tekrar aktifleştiriliyor: {ad_soyad}")
                        await self.repo.update(existing['id'], aktif=True)
                        return existing['id']

                # DB Insert
                sofor_id = await self.repo.add(
                    ad_soyad=ad_soyad,
                    telefon=telefon,
                    ehliyet_sinifi=ehliyet_sinifi,
                    ise_baslama=ise_baslama or "",
                    manual_score=manual_score,
                    score=manual_score, # Initial score is manual
                    notlar=notlar
                )

                logger.info(f"Şoför eklendi: {ad_soyad} (ID: {sofor_id})")
                return sofor_id

            except Exception as e:
                logger.error(f"Şoför ekleme hatası: {e}", exc_info=True)
                raise

    async def get_all_paged(
        self,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        search: Optional[str] = None,
        ehliyet_sinifi: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None
    ) -> List[Dict]:
        """Sayfalı ve filtreli şoför listesi"""
        # Pass additional filters
        filters = {}
        if ehliyet_sinifi: filters["ehliyet_sinifi"] = ehliyet_sinifi
        if min_score is not None: filters["score_ge"] = min_score
        if max_score is not None: filters["score_le"] = max_score

        rows = await self.repo.get_all(
            offset=skip,
            limit=limit,
            sadece_aktif=aktif_only,
            search=search,
            filters=filters
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

    async def get_by_id(self, sofor_id: int) -> Optional[Dict]:
        """ID ile şoför getir"""
        return await self.repo.get_by_id(sofor_id)

    @publishes(EventType.SOFOR_UPDATED)
    async def update_sofor(self, sofor_id: int, **kwargs) -> bool:
        """Şoför güncelle (Safe Name Change)"""
        try:
            # Ad soyad varsa title case yap
            if 'ad_soyad' in kwargs and kwargs['ad_soyad']:
                ad_soyad = ' '.join(
                    word.capitalize() for word in kwargs['ad_soyad'].strip().split()
                )
                kwargs['ad_soyad'] = ad_soyad
                
                async with self._lock:
                    existing = await self.repo.get_by_name(ad_soyad)
                    if existing and existing['id'] != sofor_id:
                        raise ValueError(f"Bu isim başka bir şoföre ait: {ad_soyad}")

            # Recalculate hybrid score if manual_score is updated
            if 'manual_score' in kwargs:
                current = await self.repo.get_by_id(sofor_id)
                if current:
                    new_score = await self.calculate_hybrid_score(sofor_id, kwargs['manual_score'])
                    kwargs['score'] = new_score

            success = await self.repo.update(sofor_id, **kwargs)
            if success:
                logger.info(f"Şoför güncellendi: ID {sofor_id}")
            return success
        except Exception as e:
            logger.error(f"Şoför güncelleme hatası: {e}")
            raise

    @publishes(EventType.SOFOR_DELETED)
    async def delete_sofor(self, sofor_id: int) -> bool:
        """Şoför sil (Smart Delete: Active->Passive, Passive->Hard)"""
        try:
            # 1. Mevcut durumu kontrol et
            current = await self.repo.get_by_id(sofor_id)
            if not current:
                return False

            if current.get('aktif'):
                # Soft Delete (Pasife çek)
                success = await self.repo.update(sofor_id, aktif=False)
                if success:
                    logger.info(f"Şoför pasife alındı (Soft Deleted): ID {sofor_id}")
                return success
            else:
                # Hard Delete (Tamamen sil)
                try:
                    success = await self.repo.hard_delete(sofor_id)
                    if success:
                        logger.info(f"Şoför tamamen silindi (Hard Deleted): ID {sofor_id}")
                    return success
                except Exception as e:
                    logger.warning(f"Hard delete engellendi (Bağımlı veri): {e}")
                    raise ValueError("Bu şoföre ait aktif/arşivlenmiş sefer kayıtları bulunduğu için tamamen silinemez. Pasif durumda kalması güvenlidir.")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Şoför silme hatası: {e}")
            raise ValueError("Şoför silinirken bir hata oluştu.")



    async def update_score(self, sofor_id: int, score: float) -> bool:
        """Sürücü manuel puanını güncelle ve hibrit puanı hesapla"""
        if score < 0.1 or score > 2.0:
            raise ValueError("Puan 0.1 ile 2.0 arasında olmalıdır")

        try:
            current = await self.repo.get_by_id(sofor_id)
            if not current:
                raise ValueError("Şoför bulunamadı")
                
            # Performans bazlı yeni hibrit puanı hesapla
            hybrid_score = await self.calculate_hybrid_score(sofor_id, score)
            
            success = await self.repo.update(sofor_id, manual_score=score, score=hybrid_score)
            if success:
                logger.info(f"Şoför puanları güncellendi: ID {sofor_id} | Manuel: {score}, Hibrit: {hybrid_score}")
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
            stats_list = await self.repo.get_sefer_stats(sofor_id=sofor_id)
            if not stats_list or len(stats_list) == 0:
                # Veri yoksa sadece manuel puanı baz al
                return manual_score

            stats = stats_list[0]
            avg_tuketim = stats.get('ort_tuketim', 0)
            
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
            hybrid = (perf_score * 0.6) + (manual_score * 0.4)
            return round(hybrid, 2)
            
        except Exception as e:
            logger.error(f"Hibrit puan hesaplama hatası: {e}")
            return manual_score

    async def bulk_add_sofor(self, data_list: List[Dict]) -> int:
        """Toplu şoför oluştur (N+1 çözüm)"""
        if not data_list:
            return 0

        # Mevcut isimleri çek (N+1 önlemi)
        existing_names = await self.repo.get_aktif_isimler()
        existing_set = set(existing_names)

        to_add = []
        to_add = []
        for data in data_list:
            # Handle Pydantic models vs Dicts
            if hasattr(data, "model_dump"):
                d = data.model_dump()
            elif hasattr(data, "dict"):
                 d = data.dict()
            else:
                d = data

            ad_soyad = d.get('ad_soyad', '').strip()
            if not ad_soyad or len(ad_soyad) < 3:
                continue
            
            # Title case
            ad_soyad = ' '.join(word.capitalize() for word in ad_soyad.split())
            
            if ad_soyad in existing_set:
                continue
            
            to_add.append({
                "ad_soyad": ad_soyad,
                "telefon": d.get("telefon", ""),
                "ise_baslama": d.get("ise_baslama", ""),
                "ehliyet_sinifi": d.get("ehliyet_sinifi", "E"),
                "notlar": d.get("notlar", ""),
                "aktif": True,
                "score": 1.0
            })

        if to_add:
            ids = await self.repo.bulk_create(to_add)
            logger.info(f"Toplu şoför eklendi: {len(ids)} adet")
            return len(ids)
        
        return 0


# Thread-safe singleton
def get_sofor_service() -> SoforService:
    from app.core.container import get_container
    return get_container().sofor_service
