import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "lojinext.db"
BACKUP_DIR = "backups"


def backup_database():
    if not os.path.exists(DB_PATH):
        print("⚠ No database file found to backup.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, f"lojinext_backup_{timestamp}.db")

    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        exit(1)


def reset_database():
    if not os.path.exists(DB_PATH):
        print("❌ Database not found.")
        return

    print(f"Connecting to database: {DB_PATH}")

    # 1. Backup
    backup_database()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("⚠ WARNING: This will DELETE all operation data (Trips, Fuel, Analysis).")

        print("Deleting Analysis Data (Anomalies)...")
        # Check if table exists first to avoid error if schema changed
        try:
            cursor.execute("DELETE FROM anomalies")
        except sqlite3.OperationalError:
            print("⚠ Table 'anomalies' not found, skipping.")

        print("Deleting Fuel Data (Yakit Alimlari)...")
        cursor.execute("DELETE FROM yakit_alimlari")

        print("Deleting Trip Data (Seferler)...")
        cursor.execute("DELETE FROM seferler")

        conn.commit()
        print("✅ Database reset successful. System is ready for Cold Start.")

        # Verify counts
        trip_count = cursor.execute("SELECT COUNT(*) FROM seferler").fetchone()[0]
        fuel_count = cursor.execute("SELECT COUNT(*) FROM yakit_alimlari").fetchone()[0]
        driver_count = cursor.execute("SELECT COUNT(*) FROM soforler").fetchone()[0]

        print(
            f"Stats -> Trips: {trip_count}, Fuel: {fuel_count}, Drivers: {driver_count} (Should be preserved)"
        )

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    reset_database()
