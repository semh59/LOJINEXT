import asyncio
from sqlalchemy import inspect
from app.database.connection import engine


async def check_columns():
    async with engine.connect() as conn:

        def get_cols(connection):
            inspector = inspect(connection)
            return inspector.get_columns("lokasyonlar")

        columns = await conn.run_sync(get_cols)
        print("Columns in 'lokasyonlar' table:")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")


if __name__ == "__main__":
    asyncio.run(check_columns())
