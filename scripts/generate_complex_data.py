
import sqlite3
import random
from datetime import datetime, timedelta
import sys

# Veritabanı yolu
DB_PATH = "d:/PROJECT/excel/app/data/yakit_takip.db"

def create_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def clear_data(conn, arac_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM yakit_alimlari WHERE arac_id = ?", (arac_id,))
    cur.execute("DELETE FROM seferler WHERE arac_id = ?", (arac_id,))
    cur.execute("DELETE FROM yakit_periyotlari WHERE arac_id = ?", (arac_id,))
    conn.commit()
    print(f"Araç {arac_id} için eski veriler temizlendi.")

def generate_complex_data():
    conn = create_connection()
    cur = conn.cursor()
    
    # 1. Araç Seç (veya oluştur)
    plaka = "34 TEST 99"
    cur.execute("INSERT OR IGNORE INTO araclar (plaka, marka, model, yil, tank_kapasitesi, hedef_tuketim, aktif) VALUES (?, 'Volvo', 'FH500', 2023, 600, 30.0, 1)", (plaka,))
    conn.commit()
    
    cur.execute("SELECT id FROM araclar WHERE plaka = ?", (plaka,))
    arac_id = cur.fetchone()[0]
    
    # Verileri temizle
    clear_data(conn, arac_id)
    
    # 2. Simülasyon Parametreleri
    start_date = datetime.now() - timedelta(days=60)
    current_date = start_date
    current_km = 120000
    
    # Depo Durumu (Simüle edilen gerçek)
    tank_capacity = 600
    current_fuel_level = 300 # Yarım depo ile başla
    
    # Tüketim Profili
    base_consumption_empty = 24.0 # L/100km (Boş)
    base_consumption_loaded = 34.0 # L/100km (Dolu)
    
    print(f"Simülasyon Başlıyor: {plaka}")
    print(f"Başlangıç KM: {current_km}, Yakıt: {current_fuel_level}L")
    
    trips = []
    fuel_logs = []
    
    # 60 gün simülasyonu
    for day in range(60):
        current_date += timedelta(days=1)
        
        # Günlük Aktivite: 1 Sefer (Gidiş veya Dönüş)
        is_loaded = random.choice([True, False])
        mesafe = random.randint(300, 700)
        
        # Gerçek Tüketim Hesabı (Fizik motoru)
        # Yük + Rastgelelik (Hava, Trafik vs %10 sapma)
        consumption_rate = base_consumption_loaded if is_loaded else base_consumption_empty
        variation = random.uniform(0.95, 1.15) # %5 iyi - %15 kötü koşullar
        real_consumption_rate = consumption_rate * variation
        
        fuel_burned = (mesafe * real_consumption_rate) / 100
        
        # Depo kontrolü: Yakıt yetecek mi?
        # Güvenlik payı: Depoda en az 50L kalsın isteriz
        needed_fuel = fuel_burned + 50
        
        # YAKIT ALIMI (Eğer gerekirse)
        if current_fuel_level < needed_fuel:
            # Şoför davranışı: Depoyu asla fullemez, "yetecek kadar" veya "bütçe kadar" alır
            # Genelde 100L - 400L arası rastgele alır
            
            # Rastgele miktar
            amount_to_add = random.randint(150, 450)
            
            # Kapasite taşmasın
            if current_fuel_level + amount_to_add > tank_capacity:
                amount_to_add = tank_capacity - current_fuel_level - 10 # Biraz boşluk bırakır
            
            # DB Kaydı
            price = random.uniform(40.0, 45.0)
            cur.execute("""
                INSERT INTO yakit_alimlari (tarih, arac_id, istasyon, fiyat_tl, litre, toplam_tutar, km_sayac, fis_no, durum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                current_date.strftime("%Y-%m-%d"),
                arac_id,
                random.choice(["Shell", "Opet", "BP", "Petrol Ofisi"]),
                price, # Fiyat
                round(amount_to_add, 2),
                round(amount_to_add * price, 2), # Toplam Tutar
                current_km, # Yakıtı sefere çıkmadan önce aldı (veya sefer arası)
                f"FIS{day}",
                "Tamam"
            ))
            fuel_logs.append(amount_to_add)
            current_fuel_level += amount_to_add
            print(f"  [YAKIT] {current_date.strftime('%d.%m')} - {amount_to_add:.1f}L Alındı. Depo: {current_fuel_level:.1f}L")
            
        # SEFER YAPILIYOR
        current_fuel_level -= fuel_burned
        old_km = current_km
        current_km += mesafe
        
        tonaj = random.randint(15000, 26000) if is_loaded else 0
        
        cur.execute("""
            INSERT INTO seferler (tarih, saat, arac_id, sofor_id, cikis_yeri, varis_yeri, mesafe_km, net_kg, ton, durum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            current_date.strftime("%Y-%m-%d"),
            "08:00",
            arac_id,
            1, # Varsayılan şoför
            "Istanbul" if day % 2 == 0 else "Ankara",
            "Ankara" if day % 2 == 0 else "Istanbul",
            mesafe,
            tonaj,
            tonaj / 1000.0,
            "Tamam"
        ))
        trips.append(fuel_burned)
        print(f"  [SEFER] {current_date.strftime('%d.%m')} - {mesafe}km ({'Dolu' if is_loaded else 'Boş'}). Yakan: {fuel_burned:.1f}L. Kalan: {current_fuel_level:.1f}L")

    conn.commit()
    print("\n--- Simülasyon Tamamlandı ---")
    print(f"Toplam Yol: {current_km - 120000} km")
    print("Simülasyonu veritabanına işledim. Şimdi AnalizService bu 'Parçalı' veriyi işlemeli.")

if __name__ == "__main__":
    generate_complex_data()
