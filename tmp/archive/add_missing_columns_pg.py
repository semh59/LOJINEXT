import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def add_columns():
    async with engine.begin() as conn:
        print("Adding columns if not exist...")
        # Postgres syntax for IF NOT EXISTS is slightly different for columns in older versions,
        # but ADD COLUMN IF NOT EXISTS is supported in modern Postgres (9.6+).

        try:
            await conn.execute(
                text(
                    "ALTER TABLE lokasyonlar ADD COLUMN IF NOT EXISTS flat_distance_km FLOAT DEFAULT 0;"
                )
            )
            print("Added flat_distance_km to lokasyonlar")
        except Exception as e:
            print(f"Error lokasyonlar: {e}")

        try:
            await conn.execute(
                text(
                    "ALTER TABLE seferler ADD COLUMN IF NOT EXISTS flat_distance_km FLOAT DEFAULT 0;"
                )
            )
            print("Added flat_distance_km to seferler")
        except Exception as e:
            print(f"Error seferler: {e}")


if __name__ == "__main__":
    asyncio.run(add_columns())
