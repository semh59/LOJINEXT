"""
TIR Yakıt Takip Sistemi - Veritabanı Yöneticisi
SQLite veritabanı işlemleri
SECURITY: Bcrypt password hashing, SQL injection protection

DEPRECATED: Bu modül legacy uyumluluk için korunmaktadır.
Yeni kod için Repository pattern kullanın.
"""
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# from config import DB_PATH  # Removed: Moving to PostgreSQL

# Load environment variables
load_dotenv()

# Setup logging
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Legacy Veritabanı Yöneticisi.
    
    DEPRECATED: Bu sınıf God Class anti-pattern'idir. 
    Tüm metodlar ilgili Repository'lere (AracRepo, SeferRepo vs.) yönlendirilmiştir (Proxy Pattern).
    PostgreSQL geçişi sonrası SQLite bağımlılığı kaldırılmıştır.
    
    NOT: threading.RLock kaldırıldı - async context'te anlamsız.
    """

    def __init__(self):
        self.db_path = None
        # REMOVED: self._lock = threading.RLock() 
        # Async context'te threading lock anlamsız. Eğer senkronizasyon 
        # gerekiyorsa asyncio.Lock kullanılmalıdır.
        # self._init_database()  # DEPRECATED: PostgreSQL için Alembic migrasyonları kullanılmalı.

    @contextmanager
    def get_connection(self):
        """
        Delegates to database.connection.get_connection().
        self.db_path is now ignored in favor of global configuration or injected singleton.
        """
        from app.database.connection import get_connection
        with get_connection() as conn:
            yield conn

    def _init_database(self):
        """Veritabanı tablolarını oluştur - Delegate to SchemaManager"""
        from app.database.schema_manager import SchemaManager
        SchemaManager.init_database()

    def _create_users_table(self, cursor):
        """Deprecated: Handled by SchemaManager"""
        pass

    def _create_default_admin(self, cursor):
        """Deprecated: Handled by SchemaManager"""
        pass

    def _insert_demo_data(self, cursor):
        """Deprecated: Handled by SchemaManager"""
        pass

    # =========================================================================
    # REPO DELEGATIONS (WITH EXPLICIT SIGNATURES)
    # =========================================================================

    # --- ARAÇ ---
    # --- ARAÇ ---
    async def get_araclar(self, sadece_aktif: bool = True) -> List[Dict]:
        from app.database.repositories.arac_repo import get_arac_repo
        return await get_arac_repo().get_all(sadece_aktif=sadece_aktif)

    async def get_arac_by_id(self, arac_id: int) -> Optional[Dict]:
        from app.database.repositories.arac_repo import get_arac_repo
        return await get_arac_repo().get_by_id(arac_id)

    async def get_arac_by_plaka(self, plaka: str) -> Optional[Dict]:
        from app.database.repositories.arac_repo import get_arac_repo
        return await get_arac_repo().get_by_plaka(plaka)

    async def add_arac(self, plaka: str, marka: str, model: str = "", yil: int = 2020,
                 tank_kapasitesi: int = 600, hedef_tuketim: float = 32.0, notlar: str = "") -> int:
        from app.database.repositories.arac_repo import get_arac_repo
        return await get_arac_repo().add(
            plaka=plaka, marka=marka, model=model, yil=yil,
            tank_kapasitesi=tank_kapasitesi, hedef_tuketim=hedef_tuketim, notlar=notlar
        )

    # --- ŞOFÖR ---
    # --- ŞOFÖR ---
    async def get_soforler(self, sadece_aktif: bool = True) -> List[Dict]:
        from app.database.repositories.sofor_repo import get_sofor_repo
        return await get_sofor_repo().get_all(sadece_aktif=sadece_aktif)

    async def get_sofor_by_id(self, sofor_id: int) -> Optional[Dict]:
        from app.database.repositories.sofor_repo import get_sofor_repo
        return await get_sofor_repo().get_by_id(sofor_id)

    async def add_sofor(self, ad_soyad: str, telefon: str = "", ise_baslama: str = "",
                  ehliyet_sinifi: str = "E", notlar: str = "") -> int:
        from app.database.repositories.sofor_repo import get_sofor_repo
        return await get_sofor_repo().add(
            ad_soyad=ad_soyad, telefon=telefon, ise_baslama=ise_baslama,
            ehliyet_sinifi=ehliyet_sinifi, notlar=notlar
        )

    async def delete_sofor(self, sofor_id: int) -> bool:
        from app.database.repositories.sofor_repo import get_sofor_repo
        return await get_sofor_repo().delete(sofor_id)

    # --- LOKASYON ---
    def get_lokasyonlar(self) -> List[Dict]:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        return get_lokasyon_repo().get_all()

    def get_lokasyon_by_id(self, lokasyon_id: int) -> Optional[Dict]:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        return get_lokasyon_repo().get_by_id(lokasyon_id)

    def get_lokasyon_mesafe(self, cikis: str, varis: str) -> int:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        return get_lokasyon_repo().get_mesafe(cikis, varis) or 0

    def get_lokasyon_by_route(self, cikis: str, varis: str) -> Optional[Dict]:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        return get_lokasyon_repo().get_by_route(cikis, varis)

    def get_benzersiz_lokasyonlar(self) -> List[str]:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        return get_lokasyon_repo().get_benzersiz_lokasyonlar()

    def add_lokasyon(self, cikis_yeri: str, varis_yeri: str, mesafe_km: int,
                     tahmini_sure: float = None, zorluk: str = "Normal",
                     cikis_lat: float = None, cikis_lon: float = None,
                     varis_lat: float = None, varis_lon: float = None,
                     api_mesafe_km: int = None, api_sure_saat: float = None,
                     ascent_m: float = None, descent_m: float = None) -> int:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        return get_lokasyon_repo().add(
            cikis_yeri=cikis_yeri, varis_yeri=varis_yeri, mesafe_km=mesafe_km,
            tahmini_sure=tahmini_sure, zorluk=zorluk,
            cikis_lat=cikis_lat, cikis_lon=cikis_lon,
            varis_lat=varis_lat, varis_lon=varis_lon,
            api_mesafe_km=api_mesafe_km, api_sure_saat=api_sure_saat,
            ascent_m=ascent_m, descent_m=descent_m
        )

    def update_lokasyon(self, lokasyon_id: int, **kwargs):
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        get_lokasyon_repo().update(lokasyon_id, **kwargs)

    def delete_lokasyon(self, lokasyon_id: int) -> bool:
        from app.database.repositories.lokasyon_repo import get_lokasyon_repo
        return get_lokasyon_repo().delete(lokasyon_id)

    # --- SEFER ---
    async def add_sefer(self, tarih: str, arac_id: int, sofor_id: int,
                  mesafe_km: int, net_kg: int, cikis_yeri: str, varis_yeri: str,
                  saat: str = "", bos_sefer: int = 0,
                  ascent_m: float = 0, descent_m: float = 0) -> int:
        from app.database.repositories.sefer_repo import get_sefer_repo
        return await get_sefer_repo().add(
            tarih=tarih, arac_id=arac_id, sofor_id=sofor_id,
            mesafe_km=mesafe_km, net_kg=net_kg,
            cikis_yeri=cikis_yeri, varis_yeri=varis_yeri,
            saat=saat, bos_sefer=bos_sefer,
            ascent_m=ascent_m, descent_m=descent_m
        )

    def delete_sefer(self, sefer_id: int) -> bool:
        from app.database.repositories.sefer_repo import get_sefer_repo
        return get_sefer_repo().delete(sefer_id)

    async def get_seferler(self, tarih=None, arac_id=None, limit=100) -> List[Dict]:
        from app.database.repositories.sefer_repo import get_sefer_repo
        return await get_sefer_repo().get_all(tarih=tarih, arac_id=arac_id, limit=limit)

    def get_bugunun_seferleri(self) -> List[Dict]:
        from app.database.repositories.sefer_repo import get_sefer_repo
        return get_sefer_repo().get_bugunun_seferleri()

    def get_sefer_by_id(self, id: int) -> Optional[Dict]:
        from app.database.repositories.sefer_repo import get_sefer_repo
        return get_sefer_repo().get_by_id_with_details(id)

    def update_sefer(self, id: int, **kwargs) -> bool:
        from app.database.repositories.sefer_repo import get_sefer_repo
        return get_sefer_repo().update_sefer(id, **kwargs)

    def get_training_seferler(self, arac_id: int, limit: int = 200) -> List[Dict]:
        from app.database.repositories.sefer_repo import get_sefer_repo
        return get_sefer_repo().get_for_training(arac_id, limit)

    def update_trips_fuel_data(self, trips: List[Any]):
        from app.database.repositories.sefer_repo import get_sefer_repo
        get_sefer_repo().update_trips_fuel_data(trips)

    # --- YAKIT ---
    async def add_yakit_alimi(self, tarih: str, arac_id: int, istasyon: str,
                        fiyat: float, litre: float, km_sayac: int, fis_no: str = "",
                        depo_durumu: str = "Bilinmiyor") -> int:
        from app.database.repositories.yakit_repo import get_yakit_repo
        return get_yakit_repo().add(
            tarih=tarih, arac_id=arac_id, istasyon=istasyon,
            fiyat=fiyat, litre=litre, km_sayac=km_sayac,
            fis_no=fis_no, depo_durumu=depo_durumu
        )


    async def get_yakit_alimlari(self, arac_id=None, limit=100) -> List[Dict]:
        from app.database.repositories.yakit_repo import get_yakit_repo
        return await get_yakit_repo().get_all(arac_id=arac_id, limit=limit)

    async def get_son_km(self, arac_id: int) -> int:
        from app.database.repositories.yakit_repo import get_yakit_repo
        return await get_yakit_repo().get_son_km(arac_id) or 0

    async def delete_yakit_alimi(self, yakit_id: int) -> bool:
        from app.database.repositories.yakit_repo import get_yakit_repo
        return await get_yakit_repo().delete(yakit_id)

    async def update_yakit_alimi(self, id: int, **kwargs) -> bool:
        from app.database.repositories.yakit_repo import get_yakit_repo
        return await get_yakit_repo().update_yakit(id, **kwargs)

    async def get_yakit_by_id(self, id: int) -> Optional[Dict]:
        from app.database.repositories.yakit_repo import get_yakit_repo
        return await get_yakit_repo().get_by_id(id)

    async def save_fuel_periods(self, periods: List[Any], clear_existing: bool = False):
        from app.database.repositories.yakit_repo import get_yakit_repo
        await get_yakit_repo().save_fuel_periods(periods, clear_existing)

    async def get_fuel_periods(self, arac_id: int, limit: int = 20) -> List[Dict]:
        from app.database.repositories.yakit_repo import get_yakit_repo
        return await get_yakit_repo().get_fuel_periods(arac_id, limit)

    # --- AYARLAR ---
    def get_ayar(self, anahtar: str, varsayilan: Any = None) -> Any:
        from app.database.repositories.config_repo import get_config_repo
        return get_config_repo().get_value(anahtar, varsayilan)

    def set_ayar(self, anahtar: str, deger: str, aciklama: str = ""):
        from app.database.repositories.config_repo import get_config_repo
        get_config_repo().set_value(anahtar, deger, aciklama)

    # --- KULLANICI ---
    def get_kullanicilar(self, sadece_aktif: bool = False) -> List[Dict]:
        from app.database.repositories.kullanici_repo import get_kullanici_repo
        return get_kullanici_repo().get_all(sadece_aktif)

    # add_user usually has args
    def add_user(self, kullanici_adi: str, sifre: str, ad_soyad: str = "", rol: str = "user") -> int:
        from app.database.repositories.kullanici_repo import get_kullanici_repo
        return get_kullanici_repo().add(
            kullanici_adi=kullanici_adi, sifre=sifre, ad_soyad=ad_soyad, rol=rol
        )

    def delete_user(self, user_id: int) -> bool:
        from app.database.repositories.kullanici_repo import get_kullanici_repo
        return get_kullanici_repo().delete(user_id)

    def update_user(self, user_id: int, **kwargs) -> bool:
        from app.database.repositories.kullanici_repo import get_kullanici_repo
        return get_kullanici_repo().update_kullanici(user_id, **kwargs)

    def get_kullanici(self, kullanici_adi: str) -> Optional[Dict]:
        from app.database.repositories.kullanici_repo import get_kullanici_repo
        return get_kullanici_repo().get_by_username(kullanici_adi)

    def verify_login(self, *args, **kwargs):
        from app.database.repositories.kullanici_repo import get_kullanici_repo
        return get_kullanici_repo().verify_login(*args, **kwargs)

    # Aliases
    add_kullanici = add_user
    update_kullanici = update_user
    delete_kullanici = delete_user
    get_kullanicilar_exclude_admin = get_kullanicilar

    # --- ANALIZ ---
    async def save_model_params(self, arac_id: int, params: Dict[str, Any]):
        from app.database.repositories.analiz_repo import get_analiz_repo
        await get_analiz_repo().save_model_params(arac_id, params)

    async def get_model_params(self, arac_id: int) -> Optional[Dict]:
        from app.database.repositories.analiz_repo import get_analiz_repo
        return await get_analiz_repo().get_model_params(arac_id)


# Global Singleton for legacy compatibility
_db_instance: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    """Legacy singleton accessor"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
