import sys
import os
import shutil
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Robust path setup
current_file_path = os.path.abspath(__file__)
script_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(script_dir)  # D:\PROJECT\LOJINEXT

if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Debug: Project Root: {project_root}")
print(f"Debug: sys.path: {sys.path}")

try:
    from app.core.config import settings
except ImportError as e:
    print(f"❌ critical import error: {e}")
    print("Ensure you are running from project root or scripts folder.")
    sys.exit(1)


def backup_database():
    """Creates a timestamped backup of the SQLite database."""
    # Assuming standard SQLite path or from config if extractable
    # For robust backup, we use the file path directly if local sqlite

    if "sqlite" in settings.DATABASE_URL:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        # Remove ./ if present
        if db_path.startswith("./"):
            db_path = db_path[2:]

        full_db_path = os.path.join(project_root, db_path)

        if not os.path.exists(full_db_path):
            # Try relative to current dir
            full_db_path = db_path
            if not os.path.exists(full_db_path):
                print(f"⚠ Database file not found at {full_db_path}. Skipping backup.")
                return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(project_root, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        backup_filename = f"lojinext_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            shutil.copy2(full_db_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            sys.exit(1)
    else:
        print("ℹ Non-SQLite database detected. Skipping file-based backup via script.")


def reset_database():
    """
    Resets the database for production/cold-start testing.
    Deletes: Sefer, Yakit, Analiz (and related)
    Keeps: Kullanici, Arac, Sofor
    """
    print(f"Connecting to database: {settings.masked_database_url}")

    # 1. Auto-Backup
    backup_database()

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("⚠ WARNING: This will DELETE all operation data (Trips, Fuel, Analysis).")
        print("Keep: Users, Vehicles, Drivers.")

        # Confirmation check (Safety)
        # Bypassed if FORCE env var is set
        if os.getenv("FORCE_RESET") != "true":
            confirm = input(
                "Are you sure? This cannot be undone. (Type 'DELETE' to confirm): "
            )
            if confirm != "DELETE":
                print("Operation cancelled.")
                return

        print("Deleting Analysis Data...")
        db.execute(text("DELETE FROM analiz_sonuclari"))

        print("Deleting Fuel Data...")
        db.execute(text("DELETE FROM yakit_kayitlari"))

        print("Deleting Trip Data...")
        db.execute(text("DELETE FROM seferler"))

        db.commit()
        print("✅ Database reset successful. System is ready for Cold Start.")

        # Verify counts
        trip_count = db.execute(text("SELECT COUNT(*) FROM seferler")).scalar()
        fuel_count = db.execute(text("SELECT COUNT(*) FROM yakit_kayitlari")).scalar()
        driver_count = db.execute(text("SELECT COUNT(*) FROM soforler")).scalar()

        print(
            f"Stats -> Trips: {trip_count}, Fuel: {fuel_count}, Drivers: {driver_count} (Should be preserved)"
        )

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()
