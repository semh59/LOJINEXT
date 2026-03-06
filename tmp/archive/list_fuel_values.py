import asyncio
from app.database.connection import AsyncSessionLocal
from sqlalchemy import text


async def list_values():
    async with AsyncSessionLocal() as session:
        print("--- Unique values in depo_durumu ---")
        res = await session.execute(
            text(
                "SELECT depo_durumu, COUNT(*) FROM yakit_alimlari GROUP BY depo_durumu"
            )
        )
        for row in res:
            print(f"'{row[0]}': {row[1]}")

        print("\n--- Unique values in durum ---")
        res = await session.execute(
            text("SELECT durum, COUNT(*) FROM yakit_alimlari GROUP BY durum")
        )
        for row in res:
            print(f"'{row[0]}': {row[1]}")


if __name__ == "__main__":
    asyncio.run(list_values())
