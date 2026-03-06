import asyncio
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.database.connection import engine


async def fix_database():
    async with engine.begin() as conn:
        print("Veritabanı dürüstlük düzeltmesi başlatılıyor...")

        # 1. Kolon kontrolü ve ekleme (PostgreSQL syntax)
        try:
            # PostgreSQL uses column_name type, but ADD COLUMN IF NOT EXISTS is fine in 9.6+
            # Let's use a safer check for older PG versions if needed, but ADD COLUMN IF NOT EXISTS is standard.
            await conn.execute(
                text(
                    "ALTER TABLE seferler ADD COLUMN IF NOT EXISTS is_real BOOLEAN DEFAULT FALSE;"
                )
            )
            print("is_real kolonu eklendi veya zaten mevcuttu.")
        except Exception as e:
            print(f"Kolon ekleme hatası: {e}")

        # 2. Tüm mevcut verileri sentetik olarak işaretle
        await conn.execute(text("UPDATE seferler SET is_real = FALSE;"))
        print("Tüm mevcut seferler IS_REAL = FALSE olarak işaretlendi.")

        # Count check
        res = await conn.execute(text("SELECT COUNT(*) FROM seferler"))
        count = res.scalar()
        print(f"Toplam {count} sefer IS_REAL = FALSE olarak işaretlendi.")


if __name__ == "__main__":
    asyncio.run(fix_database())
