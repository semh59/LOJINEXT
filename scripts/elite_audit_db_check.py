import asyncio
import sys
import os

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.unit_of_work import UnitOfWork


async def verify_counts():
    print("--- DB Audit: Veri Sayımı Başlatılıyor ---")

    async with UnitOfWork() as uow:
        vehicles = await uow.arac_repo.count()
        drivers = await uow.sofor_repo.count()
        trips = await uow.sefer_repo.count()

    print(f"Veritabanı Araç Sayısı: {vehicles}")
    print(f"Veritabanı Şoför Sayısı: {drivers}")
    print(f"Veritabanı Sefer Sayısı: {trips}")
    print("--- Sayım Tamamlandı ---")


if __name__ == "__main__":
    asyncio.run(verify_counts())
