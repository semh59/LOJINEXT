
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from app.database.db_manager import DatabaseManager
from app.config import DB_PATH

def check_counts():
    db = DatabaseManager(Path(DB_PATH))
    with db.get_connection() as conn:
        tables = ['araclar', 'soforler', 'seferler', 'yakit_alimlari']
        print("--- Table Counts ---")
        for t in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"{t}: {count}")
            except Exception as e:
                print(f"{t}: Error ({e})")

if __name__ == "__main__":
    check_counts()
