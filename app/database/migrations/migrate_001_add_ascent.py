import sqlite3
import sys
from pathlib import Path

# Add project root to python path to import config
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

from app.config import DB_PATH

def migrate():
    print(f"Checking database at {DB_PATH}...")
    
    if not DB_PATH.exists():
        print("Database not found! It will be strictly created by the app.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check existing columns in seferler
        cursor.execute("PRAGMA table_info(seferler)")
        columns = [info[1] for info in cursor.fetchall()]
        
        print(f"Existing columns in 'seferler': {columns}")
        
        updates_made = False
        
        if 'ascent_m' not in columns:
            print("Adding 'ascent_m' column...")
            cursor.execute("ALTER TABLE seferler ADD COLUMN ascent_m REAL DEFAULT 0")
            updates_made = True
            
        if 'descent_m' not in columns:
            print("Adding 'descent_m' column...")
            cursor.execute("ALTER TABLE seferler ADD COLUMN descent_m REAL DEFAULT 0")
            updates_made = True
            
        if updates_made:
            conn.commit()
            print("Migration successful! Columns added.")
        else:
            print("No migration needed. Columns already exist.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
