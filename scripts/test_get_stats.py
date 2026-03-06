import asyncio
import sys
import os
from datetime import date, timedelta

sys.path.append(os.getcwd())

from app.database.repositories.yakit_repo import get_yakit_repo


async def test_get_stats():
    repo = get_yakit_repo()
    try:
        start = date.today() - timedelta(days=30)
        end = date.today()

        print(f"Testing get_stats with range: {start} to {end}")
        stats = await repo.get_stats(baslangic_tarih=start, bitis_tarih=end)

        print("-" * 30)
        print("YAKIT STATS TEST SONUÇLARI")
        print(f"Toplam Tüketim: {stats['total_consumption']:.2f} L")
        print(f"Toplam Mesafe: {stats['total_distance']:.2f} km")
        print(f"Ortalama Tüketim: {stats['avg_consumption']:.2f} L/100km")
        print("-" * 30)

    except Exception as e:
        import traceback

        print(f"FAILED: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_get_stats())
