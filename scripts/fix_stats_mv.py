import asyncio
from app.database.connection import engine
from sqlalchemy import text


async def fix_stats_mv():
    queries = [
        # 1. MV'yi baştan oluştur (Karakter kodlaması sorunlarını gidermek için SELECT içindeki statik stringleri tazeleyelim)
        """
        DROP MATERIALIZED VIEW IF EXISTS sefer_istatistik_mv;
        """,
        """
        CREATE MATERIALIZED VIEW sefer_istatistik_mv AS
        SELECT 
            durum,
            COUNT(*) as toplam_sefer,
            SUM(mesafe_km) as toplam_km,
            SUM(otoban_mesafe_km) as highway_km,
            SUM(ascent_m) as total_ascent,
            SUM(net_kg) / 1000.0 as total_weight,
            NOW() as last_updated
        FROM seferler
        WHERE is_real = TRUE AND is_deleted = FALSE AND durum != 'İptal'
        GROUP BY durum;
        """,
        """
        CREATE UNIQUE INDEX idx_sefer_istatistik_mv_durum ON sefer_istatistik_mv (durum);
        """,
        # 2. Mevcut verilerdeki bozuk karakterli durumları düzelt (Eğer varsa)
        "UPDATE seferler SET durum = 'Planlandı' WHERE durum LIKE 'Planland%';",
        "UPDATE seferler SET durum = 'İptal' WHERE is_deleted = TRUE;",
        "UPDATE seferler SET durum = 'Tamam' WHERE durum = 'Tamamlandı' OR durum = 'Bitti';",
        # 3. MV'yi taze verilerle doldur
        "REFRESH MATERIALIZED VIEW CONCURRENTLY sefer_istatistik_mv;",
    ]

    print("--- Fix Stats MV Script Baslatildi ---")
    async with engine.begin() as conn:
        for query in queries:
            try:
                print(f"Executing Query...")
                await conn.execute(text(query))
            except Exception as e:
                print(f"Error executing query: {e}")
                # Bazıları redundant olabilir (refresh concurrently ilk seferde hata verebilir vs)

    print("--- Stats MV Fix Tamamlandi ---")


if __name__ == "__main__":
    asyncio.run(fix_stats_mv())
