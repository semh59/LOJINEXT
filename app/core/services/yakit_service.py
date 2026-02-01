"""
TIR Yakıt Takip Sistemi - Yakıt Servisi
İş mantığı katmanı: Yakıt alım işlemleri
"""

from datetime import date
from typing import Dict, List

from app.core.entities.models import YakitAlimi, YakitAlimiCreate
from app.database.repositories.yakit_repo import get_yakit_repo
from app.database.unit_of_work import get_uow
from app.infrastructure.events.event_bus import EventType, get_event_bus, publishes
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class YakitService:
    """
    Yakıt alım işlemleri iş mantığı.
    UI ve DB arasında köprü görevi görür.
    """

    def __init__(self, repo=None, event_bus=None):
        self.repo = repo or get_yakit_repo()
        self.event_bus = event_bus or get_event_bus()

    async def _check_outlier(self, arac_id: int, litre: float, km_farki: float) -> bool:
        """İstatistiksel aykırı değer kontrolü (Z-Score)"""
        if km_farki <= 0 or litre <= 0:
            return False
            
        current_tuketim = (litre / km_farki) * 100
        
        # Aracın geçmiş ortalamasını ve standart sapmasını al
        from app.database.repositories.analiz_repo import get_analiz_repo
        analiz_repo = get_analiz_repo()
        stats = await analiz_repo.get_bulk_driver_metrics() # Basitleştirilmiş istatistik
        
        # İlgili araç için istatistikleri bul (Örnek mantık, gerçekte spesifik sorgu daha iyi)
        # Şimdilik sabit limitler ve basitleştirilmiş Z-Score
        if current_tuketim < 15 or current_tuketim > 60:
            logger.warning(f"Anomali Tespit Edildi: Arac {arac_id}, Tüketim {current_tuketim:.1f} L/100km (Sınır dışı)")
            return True
        return False

    @publishes(EventType.YAKIT_ADDED)
    async def add_yakit(self, data: YakitAlimiCreate) -> int:
        """
        Yeni yakıt alımı ekle.
        """
        try:
            async with get_uow() as uow:
                # Business Rules
                arac = await uow.arac_repo.get_by_id(data.arac_id)
                if not arac or not arac.get('aktif'):
                    raise ValueError("Pasif veya geçersiz bir araç için yakıt girişi yapılamaz.")

                if data.litre <= 0:
                    raise ValueError("Litre 0'dan büyük olmalıdır")

                if data.fiyat_tl <= 0:
                    raise ValueError("Fiyat 0'dan büyük olmalıdır")

                # Future date check
                entry_date = data.tarih if isinstance(data.tarih, date) else date.fromisoformat(data.tarih)
                if entry_date > date.today():
                     raise ValueError("İleri tarihli yakıt girişi yapılamaz")

                # Son km kontrolü
                last_km = await uow.yakit_repo.get_son_km(data.arac_id)
                if last_km and data.km_sayac < last_km:
                    raise ValueError(f"KM Sayacı düşemez! (Son: {last_km}, Girilen: {data.km_sayac})")

                # Outlier Kontrolü (Log seviyesinde)
                if last_km:
                    await self._check_outlier(data.arac_id, data.litre, data.km_sayac - last_km)

                # DB Insert via Repository
                yakit_id = await uow.yakit_repo.add(
                    tarih=data.tarih,
                    arac_id=data.arac_id,
                    istasyon=data.istasyon,
                    fiyat=float(data.fiyat_tl),
                    litre=data.litre,
                    km_sayac=data.km_sayac,
                    fis_no=data.fis_no,
                    depo_durumu=data.depo_durumu
                )

                # UoW commit - veriyi kalıcı kaydet
                await uow.commit()

                logger.info(f"Yakit alimi eklendi: ID {yakit_id}, Arac {data.arac_id}")
                return yakit_id

        except Exception as e:
            logger.error(f"Yakit ekleme hatasi: {e}", exc_info=True)
            raise

    @publishes(EventType.YAKIT_UPDATED)
    async def update_yakit(self, yakit_id: int, data: YakitAlimiCreate) -> bool:
        """Yakıt kaydı güncelle"""
        try:
            success = await self.repo.update_yakit(
                id=yakit_id,
                tarih=data.tarih,
                arac_id=data.arac_id,
                istasyon=data.istasyon,
                fiyat_tl=float(data.fiyat_tl),
                litre=data.litre,
                km_sayac=data.km_sayac,
                fis_no=data.fis_no,
                depo_durumu=data.depo_durumu
            )

            if success:
                logger.info(f"Yakit güncellendi: ID {yakit_id}")

            return success

        except Exception as e:
            logger.error(f"Yakit guncelleme hatasi: {e}")
            raise

    @publishes(EventType.YAKIT_DELETED)
    async def delete_yakit(self, yakit_id: int) -> bool:
        """Yakıt kaydı sil (Smart Delete: Active->Passive, Passive->Hard)"""
        try:
            current = await self.repo.get_by_id(yakit_id)
            if not current:
                return False

            if current.get('aktif'):
                 # Soft Delete
                 success = await self.repo.update(yakit_id, aktif=0)
                 if success:
                     logger.info(f"Yakit pasife alındı (Soft Deleted): ID {yakit_id}")
                 return success
            else:
                 # Hard Delete
                 try:
                     success = await self.repo.hard_delete(yakit_id)
                     if success:
                         logger.info(f"Yakit tamamen silindi (Hard Deleted): ID {yakit_id}")
                     return success
                 except Exception as e:
                     logger.warning(f"Hard delete engellendi: {e}")
                     raise ValueError("Yakıt kaydı silinirken teknik bir engel oluştu.")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Yakit silme hatasi: {e}")
            raise ValueError("Yakıt silinirken bir hata oluştu.")

    async def add_yakit_alimi(self, **kwargs) -> int:
        """Alias for add_yakit (backward compatibility)"""
        # Convert dict to model if kwargs provided
        if kwargs:
            try:
                # kwargs içinde tarih varsa ve date objesi ise string'e çevirme (model validator halleder)
                # Pydantic model ile validasyon
                data = YakitAlimiCreate(**kwargs)
                return await self.add_yakit(data)
            except Exception as e:
                logger.error(f"Yakit ekleme hatasi (alias): {e}")
                raise
        raise ValueError("No data provided")

    async def get_by_vehicle(self, arac_id: int, limit: int = 50) -> List[YakitAlimi]:
        """Araç yakıt geçmişini getir"""
        records = await self.repo.get_all(arac_id=arac_id, limit=limit)
        return [YakitAlimi.model_validate(dict(r)) for r in records]

    async def get_all_paged(
        self,
        skip: int = 0,
        limit: int = 100,
        aktif_only: bool = True,
        **filters
    ) -> List[YakitAlimi]:
        """
        Sayfalı ve filtreli yakıt listesi (Güvenli Katman).
        Bozuk verileri sessizce atlayarak listeyi korur.
        """
        records = await self.repo.get_all(
            offset=skip,
            limit=limit,
            include_inactive=not aktif_only,
            **filters
        )
        
        results = []
        for r in records:
            try:
                results.append(YakitAlimi.model_validate(dict(r)))
            except Exception as e:
                logger.error(f"Yakit validasyon hatasi (ID {r.get('id')}): {e}")
                continue
        return results

    async def get_all(self, limit: int = 100, vehicle_id: int = None) -> List[YakitAlimi]:
        """Legacy support for getting all records"""
        return await self.get_all_paged(limit=limit, vehicle_id=vehicle_id)

    async def get_stats(self) -> Dict:
        """Genel yakıt istatistiklerini getir"""
        from app.database.repositories.analiz_repo import get_analiz_repo
        analiz_repo = get_analiz_repo()
        stats = await analiz_repo.get_dashboard_stats()
        return {
            'toplam_yakit': stats.get('toplam_yakit', 0),
            'aylik_ort': stats.get('filo_ortalama', 0)
        }

    async def get_monthly_summary(self) -> List[Dict]:
        """Aylık yakıt tüketim özeti"""
        from app.database.repositories.analiz_repo import get_analiz_repo
        return await get_analiz_repo().get_monthly_consumption_series()

    async def bulk_add_yakit(self, yakit_list: List[YakitAlimiCreate]) -> int:
        """Toplu yakıt alımı ekle (ELITE Performance: Pre-fetch & Bulk Insert)"""
        if not yakit_list:
            return 0

        count = 0
        async with get_uow() as uow:
            try:
                # 1. Pre-fetch Data for optimization (N+1 Prevention)
                last_km_cache = {}
                active_araclar = await uow.arac_repo.get_all(sadece_aktif=True)
                for a in active_araclar:
                    last_km_cache[a['id']] = await uow.yakit_repo.get_son_km(a['id']) or 0
                
                # 2. Sort & Filter
                sorted_list = sorted(yakit_list, key=lambda x: x.tarih)
                items_to_add = []

                for data in sorted_list:
                    if data.litre <= 0:
                        continue
                    
                    current_last_km = last_km_cache.get(data.arac_id, 0)
                    if data.km_sayac < current_last_km:
                        logger.warning(f"KM hatası (Atlandı): Arac {data.arac_id}, Son KM {current_last_km}, Girilen {data.km_sayac}")
                        continue
                    
                    # Outlier kontrolü (İçeride pre-fetch olmadığı için buraya çekildi)
                    km_farki = data.km_sayac - current_last_km
                    if current_last_km > 0 and km_farki > 0:
                        tuketim = (data.litre / km_farki) * 100
                        if tuketim < 15 or tuketim > 65: # Hardcoded high-level guard
                            logger.info(f"Yüksek sapma tespiti (Bulk): {data.arac_id} - {tuketim:.1f} L/100km")

                    items_to_add.append({
                        "tarih": data.tarih,
                        "arac_id": data.arac_id,
                        "istasyon": data.istasyon,
                        "fiyat": float(data.fiyat_tl),
                        "litre": data.litre,
                        "km_sayac": data.km_sayac,
                        "fis_no": data.fis_no,
                        "depo_durumu": data.depo_durumu
                    })
                    last_km_cache[data.arac_id] = data.km_sayac

                # 3. True Bulk Insert (N+1 Query Elimination)
                if items_to_add:
                    await uow.yakit_repo.bulk_create(items_to_add)
                    await uow.commit()  # UoW commit - veriyi kalıcı kaydet
                    count = len(items_to_add)
                
            except Exception as e:
                logger.error(f"Bulk insert hatası: {e}")
                raise e

        if count > 0:
            logger.info(f"Bulk insert: {count} yakıt alımı eklendi")
        return count


def get_yakit_service() -> YakitService:
    from app.core.container import get_container
    return get_container().yakit_service
