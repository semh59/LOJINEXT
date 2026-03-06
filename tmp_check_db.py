import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def check():
    async with engine.connect() as conn:
        print("Checking tables...")
        res = await conn.execute(
            text(
                "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';"
            )
        )
        tables = [r[0] for r in res]
        print(f"Tables: {tables}")

        print("\nChecking alembic_version...")
        try:
            res = await conn.execute(text("SELECT * FROM alembic_version;"))
            versions = [r[0] for r in res]
            print(f"Alembic Versions: {versions}")
        except Exception as e:
            print(f"Error checking alembic_version: {e}")


if __name__ == "__main__":
    asyncio.run(check())
