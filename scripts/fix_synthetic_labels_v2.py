import sys
from pathlib import Path

# Path manipulation MUST be FIRST
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy import text


async def fix_synthetic_labels():
    """
    Dürüstlük Protokolü - Faz 5 Sonrası
    Mevcut tüm sentetik verileri is_real=false olarak işaretler.
    Bu, ML modellerinin gerçek olmayan bir R2 skoruna güvenmesini engeller.
    """
    # Import inside function to avoid module level import errors or circular dependencies
    from app.database.connection import SessionLocal

    db = SessionLocal()
    try:
        print("🔍 Mevcut veriler analiz ediliyor...")

        # 1. Mevcut durum
        result = db.execute(
            text("SELECT is_real, COUNT(*) FROM seferler GROUP BY is_real")
        ).fetchall()
        print(f"📊 Mevcut Durum: {dict(result)}")

        # 2. Güncelleme
        print(
            "\n🛠️ Tüm 'is_real=true' kayıtlar 'is_real=false' olarak güncelleniyor (SENTETIK)..."
        )
        db.execute(text("UPDATE seferler SET is_real = false WHERE is_real = true"))
        db.commit()

        # 3. Doğrulama
        final_result = db.execute(
            text("SELECT is_real, COUNT(*) FROM seferler GROUP BY is_real")
        ).fetchall()
        print(f"✅ İşlem Tamamlandı. Yeni Durum: {dict(final_result)}")

        print("\n🚀 Sistem artık 'Cold Start' (Gerçek Veri Bekleme) moduna hazır.")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(fix_synthetic_labels())
