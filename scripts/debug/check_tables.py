import asyncio
from sqlalchemy import text
from app.database.connection import engine


async def list_tables():
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            )
        )
        tables = result.fetchall()
        print("Existing Tables in 'public' schema:")
        for table in tables:
            print(f"- {table[0]}")

        # Check counts for main tables
        main_tables = [
            "araclar",
            "soforler",
            "seferler",
            "yakit_alimlari",
            "lokasyonlar",
            "guzergahlar",
        ]
        for table in main_tables:
            try:
                res = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = res.scalar()
                print(f"Table '{table}' row count: {count}")
            except Exception as e:
                print(f"Table '{table}' check FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(list_tables())
