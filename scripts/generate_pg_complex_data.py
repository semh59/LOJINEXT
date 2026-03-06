import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

import urllib.parse

# Database URL from .env (adapted for asyncpg)
raw_password = "!23efe25ali!"
encoded_password = urllib.parse.quote_plus(raw_password)
DATABASE_URL = (
    f"postgresql+asyncpg://postgres:{encoded_password}@localhost:5432/tir_yakit"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def clear_data(session: AsyncSession, arac_id: int):
    await session.execute(
        text("DELETE FROM yakit_alimlari WHERE arac_id = :arac_id"),
        {"arac_id": arac_id},
    )
    await session.execute(
        text("DELETE FROM seferler WHERE arac_id = :arac_id"), {"arac_id": arac_id}
    )
    await session.execute(
        text("DELETE FROM yakit_periyotlari WHERE arac_id = :arac_id"),
        {"arac_id": arac_id},
    )
    await session.commit()
    print(f"Araç ID {arac_id} için eski veriler temizlendi.")


async def generate_data():
    async with AsyncSessionLocal() as session:
        # 1. Test Aracını kontrol et veya ekle
        plaka = "34 LOJI 001"
        res = await session.execute(
            text("SELECT id FROM araclar WHERE plaka = :plaka"), {"plaka": plaka}
        )
        arac = res.fetchone()

        if not arac:
            await session.execute(
                text("""
                INSERT INTO araclar (plaka, marka, model, yil, tank_kapasitesi, hedef_tuketim, aktif) 
                VALUES (:plaka, 'Mercedes-Benz', 'Actros', 2024, 700, 28.0, true)
            """),
                {"plaka": plaka},
            )
            await session.commit()
            res = await session.execute(
                text("SELECT id FROM araclar WHERE plaka = :plaka"), {"plaka": plaka}
            )
            arac_id = res.fetchone()[0]
        else:
            arac_id = arac[0]

        await clear_data(session, arac_id)

        # 2. Simülasyon Ayarları
        start_date = datetime.now() - timedelta(days=30)
        current_km = 50000
        current_fuel = 350.0  # Başlangıç deposu

        print(f"🚀 Simülasyon Başlatıldı: {plaka} (ID: {arac_id})")

        for i in range(30):
            sim_date = start_date + timedelta(days=i)
            is_loaded = random.choice([True, False])
            distance = random.randint(300, 600)
            consumption_rate = (
                random.uniform(32, 38) if is_loaded else random.uniform(22, 26)
            )
            fuel_burned = (distance / 100) * consumption_rate

            # Yakıt alımı (Depo %20 altına düşerse)
            if current_fuel < 150:
                fuel_to_add = random.randint(400, 500)
                price = random.uniform(42.0, 45.0)
                await session.execute(
                    text("""
                    INSERT INTO yakit_alimlari (tarih, arac_id, istasyon, birim_fiyat, miktar, toplam_tutar, km, fis_no, durum)
                    VALUES (:tarih, :arac_id, :istasyon, :fiyat, :miktar, :tutar, :km, :fis, 'Tamam')
                """),
                    {
                        "tarih": sim_date,
                        "arac_id": arac_id,
                        "istasyon": "Opet Lojistik",
                        "fiyat": price,
                        "miktar": fuel_to_add,
                        "tutar": fuel_to_add * price,
                        "km": current_km,
                        "fis": f"SIM-{i}",
                    },
                )
                current_fuel += fuel_to_add
                print(f"  ⛽ {sim_date.date()} - Yakıt Alındı: {fuel_to_add:.1f}L")

            # Sefer Kaydı
            ton = random.randint(18, 25) if is_loaded else 0
            await session.execute(
                text("""
                INSERT INTO seferler (tarih, saat, arac_id, sofor_id, cikis_yeri, varis_yeri, mesafe_km, net_kg, ton, durum)
                VALUES (:tarih, '09:00', :arac_id, 1, 'Gebze', 'Ankara', :km, :kg, :ton, 'Tamam')
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
            print(
                f"  🚛 {sim_date.date()} - Sefer: {distance}km ({'Dolu' if is_loaded else 'Boş'})"
            )

        await session.commit()
        print("\n✅ Simülasyon başarıyla tamamlandı. Motorlar tam güç çalışıyor.")


if __name__ == "__main__":
    asyncio.run(generate_data())
