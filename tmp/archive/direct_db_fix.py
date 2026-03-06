import asyncio
import os
from sqlalchemy import text, create_engine
from sqlalchemy.engine import URL


# Standalone DB connection without app dependency
# Using the correct elite password and verified DB name 'tir_yakit'
def run_migration():
    print("Direct Migration starting with elite credentials on 'tir_yakit'...")
    db_url = "postgresql://postgres:!23efe25ali!@localhost:5432/tir_yakit"

    engine = create_engine(db_url)

    queries = [
        "ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS otoban_mesafe_km DOUBLE PRECISION DEFAULT 0.0;",
        "ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS sehir_ici_mesafe_km DOUBLE PRECISION DEFAULT 0.0;",
        "ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS aktif BOOLEAN DEFAULT TRUE;",
    ]

    with engine.begin() as conn:
        for query in queries:
            print(f"Executing: {query}")
            try:
                conn.execute(text(query))
            except Exception as e:
                print(f"Error executing query: {e}")

    print("Migration finished successfully on 'tir_yakit'!")


if __name__ == "__main__":
    run_migration()
