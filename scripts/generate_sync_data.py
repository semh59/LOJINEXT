from sqlalchemy import create_engine, text
import random
from datetime import datetime, timedelta
import urllib.parse

# Database URL from .env (Synchronous)
raw_password = "!23efe25ali!"
encoded_password = urllib.parse.quote_plus(raw_password)
DATABASE_URL = f"postgresql://postgres:{encoded_password}@localhost:5432/tir_yakit"

engine = create_engine(DATABASE_URL)


def generate_data():
    with engine.connect() as conn:
        # 1. Test Aracını kontrol et veya ekle
        plaka = "34 LOJI 001"
        res = conn.execute(
            text("SELECT id FROM araclar WHERE plaka = :plaka"), {"plaka": plaka}
        ).fetchone()

        if not res:
            conn.execute(
                text("""
                INSERT INTO araclar (plaka, marka, model, yil, tank_kapasitesi, hedef_tuketim, aktif) 
                VALUES (:plaka, 'Mercedes-Benz', 'Actros', 2024, 700, 28.0, true)
            """),
                {"plaka": plaka},
            )
            conn.commit()
            res = conn.execute(
                text("SELECT id FROM araclar WHERE plaka = :plaka"), {"plaka": plaka}
            ).fetchone()

        arac_id = res[0]

        # 2. Eski verileri temizle
        conn.execute(
            text("DELETE FROM yakit_alimlari WHERE arac_id = :arac_id"),
            {"arac_id": arac_id},
        )
        conn.execute(
            text("DELETE FROM seferler WHERE arac_id = :arac_id"), {"arac_id": arac_id}
        )
        conn.execute(
            text("DELETE FROM yakit_periyotlari WHERE arac_id = :arac_id"),
            {"arac_id": arac_id},
        )
        conn.commit()

        # 3. Simülasyon
        start_date = datetime.now() - timedelta(days=30)
        current_km = 50000
        current_fuel = 350.0

        print(f"🚀 Senkron Simülasyon Başlatıldı: {plaka} (ID: {arac_id})")

        for i in range(30):
            sim_date = start_date + timedelta(days=i)
            is_loaded = random.choice([True, False])
            distance = random.randint(300, 600)
            consumption_rate = (
                random.uniform(32, 38) if is_loaded else random.uniform(22, 26)
            )
            fuel_burned = (distance / 100) * consumption_rate

            if current_fuel < 150:
                fuel_to_add = random.randint(400, 500)
                price = random.uniform(42.0, 45.0)
                conn.execute(
                    text("""
                    INSERT INTO yakit_alimlari (tarih, arac_id, istasyon, birim_fiyat, miktar, toplam_tutar, km, fis_no, durum)
                    VALUES (:tarih, :arac_id, 'Opet Lojistik', :fiyat, :miktar, :tutar, :km, :fis, 'Tamam')
                """),
                    {
                        "tarih": sim_date,
                        "arac_id": arac_id,
                        "fiyat": price,
                        "miktar": fuel_to_add,
                        "tutar": fuel_to_add * price,
                        "km": current_km,
                        "fis": f"SYNC-{i}",
                    },
                )
                current_fuel += fuel_to_add
                print(f"  ⛽ {sim_date.date()} - Yakıt: +{fuel_to_add:.1f}L")

            ton = random.randint(18, 25) if is_loaded else 0
            conn.execute(
                text("""
                INSERT INTO seferler (tarih, saat, arac_id, sofor_id, cikis_yeri, varis_yeri, mesafe_km, net_kg, ton, durum)
                VALUES (:tarih, '09:00', :arac_id, 1, 'Istanbul', 'Ankara', :km, :kg, :ton, 'Tamam')
            """),
                {
                    "tarih": sim_date,
                    "arac_id": arac_id,
                    "km": distance,
                    "kg": ton * 1000,
                    "ton": ton,
                },
            )

            current_km += distance
            current_fuel -= fuel_burned
            print(f"  🚛 {sim_date.date()} - Sefer: {distance}km")

        conn.commit()
        print("\n✅ Veri enjeksiyonu tamamlandı. Sistem aktif.")


if __name__ == "__main__":
    generate_data()
