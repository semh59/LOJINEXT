"""
TIR Yakıt Takip Sistemi - OpenRouteService Client
Mesafe hesaplama, yükseklik profili ve cache yönetimi

Özellikler:
- TIR (driving-hgv) profili ile gerçekçi mesafe
- Elevation (yükseklik) desteği: bayır çıkış/iniş bilgisi
- Veritabanı tabanlı cache (API tasarrufu)
- Rate limiting (1 req/sec)
- Hata yönetimi ve fallback
"""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# HTTP client
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Load environment
from dotenv import load_dotenv

load_dotenv()

import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class OpenRouteClient:
    """
    OpenRouteService API Client
    
    Kullanım:
        client = OpenRouteClient()
        result = client.get_distance(
            origin=(40.7669, 29.4319),    # Gebze (lat, lon)
            destination=(39.9334, 32.8597) # Ankara
        )
        print(result)  
        # {'distance_km': 452.3, 'duration_hours': 5.5, 'source': 'api'}
    """

    BASE_URL = "https://api.openrouteservice.org/v2"
    PROFILE = "driving-hgv"  # Heavy Goods Vehicle (TIR)

    # Rate limiting
    _last_request_time = 0
    _rate_limit_lock = threading.Lock()
    MIN_REQUEST_INTERVAL = 1.0  # 1 saniye minimum aralık

    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: OpenRouteService API key. None ise .env dosyasından okunur.
        """
        self.api_key = api_key or os.getenv("OPENROUTE_API_KEY")

        if not self.api_key:
            logger.warning("OPENROUTE_API_KEY tanımlanmamış! API çağrıları başarısız olacak.")

        self._db = None  # Lazy loading

        # Circuit Breaker config
        self._consecutive_failures = 0
        self._circuit_open = False
        self._last_failure_time = 0
        self._reset_timeout = 60  # 60 saniye bekle
        self._failure_threshold = 5

    @property
    def db(self):
        """Deprecated: Use get_sync_session directly"""
        return None

    def _check_circuit_breaker(self) -> bool:
        """Circuit breaker durumunu kontrol et. True dönerse istek atılabilir."""
        import time
        if self._circuit_open:
            if time.time() - self._last_failure_time > self._reset_timeout:
                logger.info("Circuit breaker: Half-Open (retrying)")
                return True
            return False
        return True

    def _record_success(self):
        """Başarılı istek sonrası reset"""
        if self._consecutive_failures > 0 or self._circuit_open:
            logger.info("Circuit breaker: Closed (recovered)")
            self._consecutive_failures = 0
            self._circuit_open = False

    def _record_failure(self):
        """Hata kaydet"""
        import time
        self._consecutive_failures += 1
        self._last_failure_time = time.time()
        
        if self._consecutive_failures >= self._failure_threshold:
            if not self._circuit_open:
                logger.error(f"Circuit breaker: OPEN (Too many failures: {self._consecutive_failures})")
            self._circuit_open = True

    def get_distance(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        İki koordinat arası mesafe hesapla.
        
        Args:
            origin: (latitude, longitude) başlangıç
            destination: (latitude, longitude) varış
            use_cache: Veritabanı cache kullan (önerilir)
            
        Returns:
            {
                'distance_km': float,
                'duration_hours': float,
                'ascent_m': float,      # Toplam bayır çıkış (metre)
                'descent_m': float,     # Toplam bayır iniş (metre)
                'source': 'cache' | 'api' | 'error'
            }
            veya hata durumunda None
        """
        # Input validation
        if not self._validate_coordinates(origin, destination):
            logger.error(f"Geçersiz koordinatlar: {origin} -> {destination}")
            return None

        # 1. Cache kontrolü
        if use_cache:
            cached = self._get_from_cache(origin, destination)
            if cached:
                logger.debug(f"Cache hit: {origin} -> {destination}")
                return {**cached, 'source': 'cache'}

        # 2. API çağrısı
        if not HAS_REQUESTS:
            # requests yoksa hata dön
            logger.error("requests modülü yüklü değil! pip install requests")
            return None

        if not self.api_key:
            logger.error("API key eksik, mesafe hesaplanamadı")
            return None

        # Circuit Breaker Check
        if not self._check_circuit_breaker():
            logger.warning("Circuit breaker OPEN. Skipping API call.")
            return None

        result = self._call_api(origin, destination)

        if result:
            self._record_success()
            # 3. Cache'e kaydet
            self._save_to_cache(origin, destination, result)
            return {**result, 'source': 'api'}
        else:
            self._record_failure()

        return None

    def _validate_coordinates(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> bool:
        """Koordinatların geçerli ve Türkiye sınırları içinde olduğunu doğrula"""
        try:
            for coord in [origin, destination]:
                if not isinstance(coord, (list, tuple)) or len(coord) != 2:
                    return False
                lat, lon = coord
                # Türkiye yaklaşık sınırları
                if not (35.0 <= lat <= 43.0 and 25.0 <= lon <= 46.0):
                    return False
            return True
        except Exception:
            return False

    def _call_api(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Optional[Dict]:
        """Gerçek API çağrısını yap (Sync)"""
        if not self.api_key:
            return None

        # Rate limiting
        with self._rate_limit_lock:
            import time
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.MIN_REQUEST_INTERVAL:
                time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
            self._last_request_time = time.time()

        url = f"{self.BASE_URL}/directions/{self.PROFILE}"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        # ORS [lon, lat] bekler
        payload = {
            "coordinates": [
                [origin[1], origin[0]],
                [destination[1], destination[0]]
            ],
            "preference": "fastest",
        }

        try:
            import requests
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                summary = data["routes"][0]["summary"]
                return {
                    "distance_km": round(summary["distance"] / 1000.0, 1),
                    "duration_hours": round(summary["duration"] / 3600.0, 1),
                    "ascent_m": summary.get("ascent", 0),
                    "descent_m": summary.get("descent", 0)
                }
            else:
                logger.error(f"API Hatası: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"API Çağrı Hatası: {e}")
            return None

    def _get_from_cache(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> Optional[Dict]:
        """Veritabanından cache'lenmiş mesafe ve elevation verileri al"""
        lat1, lon1 = origin
        lat2, lon2 = destination

        # Koordinat toleransı (yaklaşık 100m)
        tolerance = 0.001

        from sqlalchemy import text

        from app.database.connection import get_sync_session

        try:
            with get_sync_session() as session:
                row = session.execute(text("""
                    SELECT api_mesafe_km, api_sure_saat, ascent_m, descent_m
                    FROM lokasyonlar
                    WHERE ABS(cikis_lat - :lat1) < :tol
                      AND ABS(cikis_lon - :lon1) < :tol
                      AND ABS(varis_lat - :lat2) < :tol
                      AND ABS(varis_lon - :lon2) < :tol
                      AND api_mesafe_km IS NOT NULL
                    LIMIT 1
                """), {
                    "lat1": lat1, "lon1": lon1,
                    "lat2": lat2, "lon2": lon2,
                    "tol": tolerance
                }).fetchone()

                if row:
                    return {
                        "distance_km": row.api_mesafe_km,
                        "duration_hours": row.api_sure_saat or 0,
                        "ascent_m": row.ascent_m or 0,
                        "descent_m": row.descent_m or 0
                    }
        except Exception as e:
            logger.error(f"Cache okuma hatası: {e}")

        return None

    def _save_to_cache(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        result: Dict
    ):
        """Mesafe ve elevation sonucunu veritabanına kaydet"""
        lat1, lon1 = origin
        lat2, lon2 = destination

        from sqlalchemy import text

        from app.database.connection import get_sync_session

        try:
            with get_sync_session() as session:
                # Mevcut kayıt var mı kontrol et
                existing = session.execute(text("""
                    SELECT id FROM lokasyonlar
                    WHERE ABS(cikis_lat - :lat1) < 0.001
                      AND ABS(cikis_lon - :lon1) < 0.001
                      AND ABS(varis_lat - :lat2) < 0.001
                      AND ABS(varis_lon - :lon2) < 0.001
                    LIMIT 1
                """), {"lat1": lat1, "lon1": lon1, "lat2": lat2, "lon2": lon2}).fetchone()

                if existing:
                    # Güncelle - elevation dahil
                    session.execute(text("""
                        UPDATE lokasyonlar 
                        SET api_mesafe_km = :dist, 
                            api_sure_saat = :dur,
                            ascent_m = :asc,
                            descent_m = :desc,
                            last_api_call = :now
                        WHERE id = :id
                    """), {
                        "dist": result["distance_km"],
                        "dur": result["duration_hours"],
                        "asc": result.get("ascent_m", 0),
                        "desc": result.get("descent_m", 0),
                        "now": datetime.now().isoformat(),
                        "id": existing.id
                    })
                    session.commit()
                    logger.debug(f"Cache güncellendi: ID {existing.id}")
                else:
                    logger.debug("Yeni güzergah için cache kaydedilecek (güzergah henüz yok)")

        except Exception as e:
            logger.error(f"Cache kayıt hatası: {e}")

    def update_route_distance(self, lokasyon_id: int) -> Optional[Dict]:
        """
        Mevcut bir güzergahın mesafesini API'den güncelle.
        """
        from sqlalchemy import text

        from app.database.connection import get_sync_session

        try:
            with get_sync_session() as session:
                row = session.execute(text("""
                    SELECT cikis_lat, cikis_lon, varis_lat, varis_lon
                    FROM lokasyonlar WHERE id = :id
                """), {"id": lokasyon_id}).fetchone()

                if not row or not all([row.cikis_lat, row.cikis_lon, row.varis_lat, row.varis_lon]):
                    logger.warning(f"Lokasyon {lokasyon_id} koordinat bilgisi eksik")
                    return None

                origin = (row.cikis_lat, row.cikis_lon)
                destination = (row.varis_lat, row.varis_lon)

                # API çağrısı (dışarıda, session tutarken API çağrısı yapmak transaction süresini uzatabilir ama burada basitlik için kabul edilebilir)
                # Ancak session'ı API çağrısından önce kapatıp sonra tekrar açmak daha iyi olabilir.
                # Fakat burada okuma ve yazma transaction içinde olduğu için ve API çağrısı ortada olduğu için,
                # veriyi okuduktan sonra session'dan çıkıp, API çağırıp, tekrar session açıp update etmek mantıklı.

            # API çağrısı
            result = self.get_distance(origin, destination, use_cache=False)

            if result:
                with get_sync_session() as session:
                    # Elevation dahil güncelle
                    session.execute(text("""
                        UPDATE lokasyonlar 
                        SET api_mesafe_km = :dist, 
                            api_sure_saat = :dur,
                            ascent_m = :asc,
                            descent_m = :desc,
                            mesafe_km = COALESCE(mesafe_km, :dist_km),
                            tahmini_sure_saat = COALESCE(tahmini_sure_saat, :dur_h),
                            last_api_call = :now
                        WHERE id = :id
                    """), {
                        "dist": result["distance_km"],
                        "dur": result["duration_hours"],
                        "asc": result.get("ascent_m", 0),
                        "desc": result.get("descent_m", 0),
                        "dist_km": result["distance_km"],
                        "dur_h": result["duration_hours"],
                        "now": datetime.now().isoformat(),
                        "id": lokasyon_id
                    })
                    session.commit()

                    logger.info(f"Güzergah {lokasyon_id} güncellendi: {result['distance_km']} km, "
                               f"↑{result.get('ascent_m', 0)}m ↓{result.get('descent_m', 0)}m")
                    return result

        except Exception as e:
            logger.error(f"Güzergah güncelleme hatası: {e}", exc_info=True)

        return None


# Singleton instance
_client_instance: Optional[OpenRouteClient] = None
_client_lock = threading.Lock()


def get_route_client() -> OpenRouteClient:
    """Thread-safe singleton getter"""
    global _client_instance
    if _client_instance is None:
        with _client_lock:
            if _client_instance is None:
                _client_instance = OpenRouteClient()
    return _client_instance
