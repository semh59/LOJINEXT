import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "skara"
PASSWORD = "!23efe25ali!"


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"🚀 {title}")
    print(f"{'=' * 60}")


def login():
    print("🔑 Admin girişi yapılıyor...")
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/token", data={"username": USERNAME, "password": PASSWORD}
        )
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            print("✅ Giriş Başarılı!")
            return {"Authorization": f"Bearer {token}"}
        else:
            print(f"❌ Giriş Hatası: {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return None


def create_route(headers):
    print_section("ADIM 1: AKILLI GÜZERGAH TANIMLAMA")
    print("ℹ️  AI'nın hava durumu ve eğimi bilmesi için güzergah tanımlıyoruz...")

    route_data = {
        "ad": "DEMO-ISTANBUL-ANKARA",
        "cikis_yeri": "Istanbul",
        "varis_yeri": "Ankara",
        "mesafe_km": 450,
        "tahmini_sure_dk": 300,
        "ascent_m": 1200,  # Bolu Dağı tırmanışı
        "descent_m": 1100,
        "aktif": True,
        # Fake coordinates for WeatherService
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 39.9334,
        "varis_lon": 32.8597,
    }

    resp = requests.post(f"{BASE_URL}/routes/", json=route_data, headers=headers)
    if resp.status_code in [200, 201]:
        data = resp.json()
        print(f"✅ Güzergah Oluşturuldu: {data['ad']} (ID: {data['id']})")
        print(f"   - Mesafe: {data['mesafe_km']} km")
        print(f"   - Tırmanış: {data['ascent_m']} m (AI bunu kullanacak)")
        return data["id"]
    else:
        print(f"⚠️ Güzergah eklenemedi (Muhtemelen var): {resp.status_code}")
        # Var olanı bulmaya çalışalım (Basitlik için ID 1 varsayalım veya listeleyelim)
        # Demo için kritik değil, ID manuel set edilecek veya hata alınacak
        return 1


def create_trip(headers, route_id):
    print_section("ADIM 2: SEFER BAŞLATMA")
    print("ℹ️  34 AB 123 plakalı araç yola çıkıyor (22 Ton Yük)...")

    # Araç ID 1 ve Şoför ID 1 varsayıyoruz (Seed datasından)
    trip_data = {
        "tarih": "2024-02-17",
        "arac_id": 1,
        "sofor_id": 1,
        "guzergah_id": route_id,
        "sefer_no": "DEMO-001",
        "mesafe_km": 450,
        "net_kg": 22000,
        "cikis_yeri": "Istanbul",
        "varis_yeri": "Ankara",
        "durum": "Tamamlandı",
    }

    resp = requests.post(f"{BASE_URL}/trips/", json=trip_data, headers=headers)
    if resp.status_code in [200, 201]:
        data = resp.json()
        print(f"✅ Sefer Oluşturuldu: {data['sefer_no']} (ID: {data['id']})")
        print(
            f"   - Tahmini Tüketim: {data.get('tahmini_tuketim', 'Hesaplanamadı')} Litre"
        )
        if data.get("tahmini_tuketim"):
            print("   ✨ AI Devreye Girdi! Tahmin üretildi.")
        return data["id"]
    else:
        print(f"❌ Sefer Hatası: {resp.text}")
        return None


def add_fuel(headers, trip_id):
    print_section("ADIM 3: YAKIT FİŞİ GİRİŞİ")
    print("ℹ️  Ankara'ya varışta yakıt alınıyor...")

    # Araç ID 1'e yakıt giriyoruz.
    # Son KM'yi çekmek lazım ama demo için direkt sefer mesafesini ekleyelim.
    # Varsayalım araç 100.000 km'deydi, şimdi 100.450 km.

    fuel_data = {
        "tarih": "2024-02-17",
        "arac_id": 1,
        "km_sayac": 100450,  # 450 km yol yaptı
        "litre": 150,  # 33 LT/100km ortalama
        "fiyat_tl": 42.5,
        "istasyon": "Ankara Petrol",
        "fis_no": "Fiş-999",
        "depo_durumu": "Full",  # Critical for precise calc
    }

    resp = requests.post(f"{BASE_URL}/fuel/", json=fuel_data, headers=headers)
    if resp.status_code in [200, 201]:
        data = resp.json()
        print(f"✅ Yakıt Fişi İşlendi: {data['litre']} LT @ {data['istasyon']}")
        return data["id"]
    else:
        print(f"❌ Yakıt Hatası: {resp.text}")
        return None


def check_analysis(headers, vehicle_id=1):
    print_section("ADIM 4: ANALİZ RAPORU (MOTOR SESİ)")
    print("ℹ️  Sistem verileri işliyor ve raporluyor...")

    # Tetiklemek için kısa bir bekleme (Async workerlar için)
    time.sleep(1)

    try:
        # Araç detaylarına bakalım, orada istatistikler var
        resp = requests.get(f"{BASE_URL}/vehicles/{vehicle_id}/stats", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("\n📊 ARAÇ KARNESİ (34 TJ 2631):")
            print(f"   - Ortalama Tüketim: {data.get('ort_tuketim')} L/100km")
            print(f"   - Verimlilik Skoru (EEI): {data.get('eei')}")
            print(f"   - Anomali Sayısı: {data.get('anomali_sayisi')}")

            if data.get("eei", 0) > 100:
                print("   🌟 SONUÇ: Araç olması gerekenden daha verimli sürülmüş!")
            else:
                print("   ⚠️ SONUÇ: Tüketim biraz yüksek, dikkat edilmeli.")
        else:
            print(f"⚠️ Analiz çekilemedi: {resp.status_code}")

    except Exception as e:
        print(f"❌ Analiz Hatası: {e}")


def main():
    print("🏎️  LOJINEXT MOTORLARI ÇALIŞTIRILIYOR...\n")
    headers = login()
    if not headers:
        return

    # Clean start for demo? No, let's just add to existing.

    route_id = create_route(headers)
    if route_id:
        trip_id = create_trip(headers, route_id)
        if trip_id:
            add_fuel(headers, trip_id)
            check_analysis(headers)

    print("\n🏁 DEMO TAMAMLANDI. SİSTEM CANLI VE ÇALIŞIYOR.")


if __name__ == "__main__":
    main()
