
import asyncio
from sqlalchemy import select
from app.database.connection import get_db
from app.database.models import Sofor

async def verify_drivers():
    async for db in get_db():
        print("--- Şoför Veritabanı Kontrolü ---")
        stmt = select(Sofor)
        result = await db.execute(stmt)
        drivers = result.scalars().all()
        
        if not drivers:
            print("Veritabanında şoför bulunamadı.")
            return

        for d in drivers:
            # Multiplier calculation (Frontend/Prediction logic check)
            multiplier = 1.0 + (1.0 - d.score) * 0.2
            multiplier = max(0.8, min(1.2, multiplier))
            
            # Star calculation logic check
            star_count = round((d.score / 2.0) * 5)
            
            print(f"ID: {d.id} | Ad: {d.ad_soyad}")
            print(f"  DB Puanı (Score): {d.score}")
            print(f"  Yıldız Karşılığı: {'★' * star_count}{'☆' * (5-star_count)}")
            print(f"  Yakit Çarpan Etkisi: {multiplier:.3f}x")
            print(f"  Durum: {'Aktif' if d.aktif else 'Pasif'}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(verify_drivers())
