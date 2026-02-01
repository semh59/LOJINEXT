"""
LojiNext AI Backend - Load Test with Locust

Kullanım:
1. pip install locust
2. locust -f scripts/locustfile.py --host http://127.0.0.1:8000
3. Tarayıcıda http://localhost:8089 aç
4. Kullanıcı sayısı ve spawn rate gir, Start Swarming
"""

from locust import HttpUser, task, between, events
import random

class LojiNextUser(HttpUser):
    """LojiNext Backend yük testi kullanıcısı"""
    
    wait_time = between(1, 3)  # İstekler arası bekleme
    
    def on_start(self):
        """Her kullanıcı için başlangıç - Auth token al"""
        # Login yapmadan çalışan endpoint'leri test ediyoruz
        pass
    
    @task(5)
    def get_vehicles(self):
        """Araç listesi - En sık çağrılan"""
        self.client.get("/api/v1/vehicles/")
    
    @task(5)
    def get_drivers(self):
        """Şoför listesi"""
        self.client.get("/api/v1/drivers/")
    
    @task(4)
    def get_trips(self):
        """Sefer listesi"""
        self.client.get("/api/v1/trips/")
    
    @task(3)
    def get_fuel(self):
        """Yakıt alımları listesi"""
        self.client.get("/api/v1/fuel/")
    
    @task(2)
    def get_dashboard(self):
        """Dashboard istatistikleri"""
        self.client.get("/api/v1/reports/dashboard")
    
    @task(2)
    def get_locations(self):
        """Lokasyonlar"""
        self.client.get("/api/v1/locations/")
    
    @task(1)
    def get_ai_status(self):
        """AI durumu"""
        self.client.get("/api/v1/ai/status")


class StressUser(HttpUser):
    """Stres testi için yoğun kullanıcı"""
    
    wait_time = between(0.1, 0.5)  # Çok kısa bekleme
    
    @task(10)
    def rapid_list_calls(self):
        """Hızlı liste çağrıları"""
        endpoints = [
            "/api/v1/vehicles/",
            "/api/v1/drivers/",
            "/api/v1/trips/",
            "/api/v1/fuel/",
            "/api/v1/locations/"
        ]
        self.client.get(random.choice(endpoints))


# Test sonuç özeti
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*60)
    print("📊 LOAD TEST SONUÇLARI")
    print("="*60)
    print(f"✅ Toplam İstek: {environment.stats.total.num_requests}")
    print(f"❌ Başarısız: {environment.stats.total.num_failures}")
    print(f"📈 RPS: {environment.stats.total.current_rps:.2f}")
    print(f"⏱️ Ortalama Yanıt: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"⚡ 95% Percentile: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
    print("="*60 + "\n")
