import sys
from pathlib import Path

# Absolute path correction
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text


def fix_synthetic_labels():
    """
    Dürüstlük Protokolü - Faz 5 Sonrası
    Mevcut tüm sentetik verileri is_real=false olarak işaretler.
    """
    try:
        # Import inside function to avoid module level import errors or circular dependencies
        from app.database.connection import SyncSessionLocal

        db = SyncSessionLocal()
        print("🔍 Mevcut veriler analiz ediliyor...")

        # 1. Mevcut durum
        result = db.execute(
            text("SELECT is_real, COUNT(*) FROM seferler GROUP BY is_real")
        ).fetchall()
        # Convert list of tuples to dict for printing
        current_status = {str(row[0]): row[1] for row in result}
        print(f"📊 Mevcut Durum: {current_status}")

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
        final_status = {str(row[0]): row[1] for row in final_result}
        print(f"✅ İşlem Tamamlandı. Yeni Durum: {final_status}")

        print("\n🚀 Sistem artık 'Cold Start' (Gerçek Veri Bekleme) moduna hazır.")
        db.close()

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        # Try to print more details from settings if possible
        try:
            from app.config import settings

            print(f"📡 DB_URL (Masked): {settings.DATABASE_URL[:20]}...")
        except:
            pass


if __name__ == "__main__":
    fix_synthetic_labels()
