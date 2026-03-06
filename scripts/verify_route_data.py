import asyncio
import os
import sys

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import AsyncSessionLocal
from sqlalchemy import text


async def verify_route_data():
    """
    Rota sapması hesaplaması için kritik olan `hedef_km` verisinin doluluk oranını kontrol eder.
    """
    async with AsyncSessionLocal() as session:
        print("\n--- Rota Verisi Doğrulama ---")

        # 1. Toplam Sefer Sayısı
        total_trips = await session.execute(text("SELECT COUNT(*) FROM seferler"))
        total = total_trips.scalar()
        print(f"Toplam Sefer: {total}")

        # 2. Hedef KM'si (Lokasyon tablosundan) olan seferler
        # Seferin guzergah_id'si var mı ve bu guzergahın mesafe_km'si dolu mu?
        valid_route_query = """
            SELECT COUNT(*) 
            FROM seferler s
            JOIN lokasyonlar l ON s.guzergah_id = l.id
            WHERE s.mesafe_km IS NOT NULL AND l.mesafe_km IS NOT NULL
        """
        valid_routes = await session.execute(text(valid_route_query))
        valid_count = valid_routes.scalar()

        coverage = (valid_count / total * 100) if total > 0 else 0
        print(f"Geçerli Rota Verisi (Hedef vs Gerçek): {valid_count} ({coverage:.1f}%)")

        if coverage < 50:
            print("⚠️ UYARI: Seferlerin yarısından fazlasında hedef rota verisi eksik!")
            print("   -> 'Rota Sapması' maliyeti olduğundan düşük hesaplanacak.")
        else:
            print("✅ Veri kapsamı yeterli.")

        # 3. Örnek Sapmalar
        print("\n--- Örnek Rota Sapmaları (Top 5) ---")
        deviation_query = """
            SELECT 
                s.sefer_no, 
                s.cikis_yeri || ' - ' || s.varis_yeri as guzergah,
                s.mesafe_km as gercek, 
                l.mesafe_km as hedef,
                (s.mesafe_km - l.mesafe_km) as sapma
            FROM seferler s
            JOIN lokasyonlar l ON s.guzergah_id = l.id
            WHERE (s.mesafe_km - l.mesafe_km) > 10
            ORDER BY sapma DESC
            LIMIT 5
        """
        rows = await session.execute(text(deviation_query))
        for row in rows:
            print(
                f"Sefer {row.sefer_no}: {row.guzergah} | Hedef: {row.hedef}km, Gerçek: {row.gercek}km, Sapma: +{row.sapma}km"
            )


if __name__ == "__main__":
    asyncio.run(verify_route_data())
