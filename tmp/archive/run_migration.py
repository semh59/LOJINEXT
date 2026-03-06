import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine.url import make_url
from app.config import settings


async def run_migration():
    url = make_url(settings.DATABASE_URL)
    if "postgresql" in url.drivername and "+asyncpg" not in url.drivername:
        url = url.set(drivername="postgresql+asyncpg")

    engine = create_async_engine(url)
    sql_path = "app/database/migrations/harden_model_versions.sql"

    if not os.path.exists(sql_path):
        print(f"Error: {sql_path} not found")
        return

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    print(f"Running migration from {sql_path}...")
    async with engine.begin() as conn:
        for command in sql.split(";"):
            cmd = command.strip()
            if cmd:
                await conn.execute(text(cmd))

    print("Migration successful")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
