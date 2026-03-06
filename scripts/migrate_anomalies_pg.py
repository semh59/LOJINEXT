import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def migrate():
    async with engine.begin() as conn:
        print("Creating 'anomalies' table in PostgreSQL...")

        statements = [
            """
            CREATE TABLE IF NOT EXISTS anomalies (
                id SERIAL PRIMARY KEY,
                tarih DATE NOT NULL,
                tip VARCHAR(50) NOT NULL,
                kaynak_tip VARCHAR(50) NOT NULL,
                kaynak_id INTEGER NOT NULL,
                deger DOUBLE PRECISION NOT NULL,
                beklenen_deger DOUBLE PRECISION NOT NULL,
                sapma_yuzde DOUBLE PRECISION NOT NULL,
                severity VARCHAR(20) NOT NULL,
                aciklama TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_anomalies_tarih ON anomalies(tarih)",
            "CREATE INDEX IF NOT EXISTS idx_anomalies_tip ON anomalies(tip)",
            "CREATE INDEX IF NOT EXISTS idx_anomalies_kaynak_id ON anomalies(kaynak_id)",
        ]

        for stmt in statements:
            try:
                await conn.execute(text(stmt))
                print(f"SUCCESS: Executed: {stmt.strip()[:50]}...")
            except Exception as e:
                print(f"FAILED: Statement fail: {e}")
                raise e


if __name__ == "__main__":
    asyncio.run(migrate())
