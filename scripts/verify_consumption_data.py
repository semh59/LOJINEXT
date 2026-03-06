import asyncio
import os
import sys

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import AsyncSessionLocal
from sqlalchemy import text


async def verify_consumption_data():
    """
    Yakıt tüketim verilerini denetler (Audit).
    1. Mantıksız tüketim değerleri (Aykırı Değerler)
    2. Tamamlanmış ama yakıtı girilmemiş seferler
    """
    async with AsyncSessionLocal() as session:
        print("\n--- Yakıt Tüketim Verisi Denetimi (Audit) ---")

        # 1. Aykırı Değerler (Outliers)
        # 100km'de 5L altı veya 100L üstü tüketimler mantıksız kabul edilir (TIR için)
        outlier_query = """
            SELECT 
                s.sefer_no, 
                a.plaka,
                s.mesafe_km, 
                s.tuketim,
                (s.tuketim / s.mesafe_km * 100) as ort_tuketim_100km
            FROM seferler s
            JOIN araclar a ON s.arac_id = a.id
            WHERE s.durum = 'Tamam' 
              AND s.mesafe_km > 10 
              AND s.tuketim > 0
              AND ((s.tuketim / s.mesafe_km * 100) > 100 OR (s.tuketim / s.mesafe_km * 100) < 5)
            ORDER BY ort_tuketim_100km DESC
        """

        rows = await session.execute(text(outlier_query))
        outliers = rows.fetchall()

        print(f"\n1. Aykırı Tüketim Değerleri: {len(outliers)} adet")
        if outliers:
            print(
                f"{'Sefer No':<15} {'Plaka':<12} {'Mesafe':<10} {'Tüketim':<10} {'Ort (L/100km)':<15}"
            )
            print("-" * 65)
            for row in outliers[:10]:  # İlk 10 tanesini göster
                print(
                    f"{row.sefer_no:<15} {row.plaka:<12} {row.mesafe_km:<10.1f} {row.tuketim:<10.1f} {row.ort_tuketim_100km:<15.1f}"
                )
            if len(outliers) > 10:
                print(f"... ve {len(outliers) - 10} kayıt daha.")
        else:
            print("✅ Aykırı değer bulunamadı.")

        # 2. Eksik Yakıt Verisi
        # Tamamlanmış (durum='Tamam') ama yakıt (tuketim) girilmemiş veya 0 olanlar
        missing_query = """
            SELECT COUNT(*) 
            FROM seferler
            WHERE durum = 'Tamam' AND (tuketim IS NULL OR tuketim = 0)
        """
        missing_result = await session.execute(text(missing_query))
        missing_count = missing_result.scalar()

        print(f"\n2. Eksik Yakıt Verisi (Tamamlanan Seferler): {missing_count} adet")

        if missing_count > 0:
            print(
                "⚠️ UYARI: Bu seferler 'Filo Sağlığı' ve 'Maliyet Kaçağı' hesaplamalarında eksik veri yaratır."
            )

            # Detaylar (İlk 5)
            detail_query = """
                SELECT s.sefer_no, s.tarih, a.plaka
                FROM seferler s
                JOIN araclar a ON s.arac_id = a.id
                WHERE s.durum = 'Tamam' AND (s.tuketim IS NULL OR s.tuketim = 0)
                ORDER BY s.tarih DESC
                LIMIT 5
            """
            details = await session.execute(text(detail_query))
            for row in details:
                print(f"   - {row.sefer_no} ({row.tarih}) - {row.plaka}")
        else:
            print("✅ Tüm tamamlanan seferlerin yakıt verisi tam.")


if __name__ == "__main__":
    asyncio.run(verify_consumption_data())
