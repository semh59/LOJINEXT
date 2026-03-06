import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings


async def check_fuel_values():
    # Sync with app.database.connection logic for asyncpg
    from sqlalchemy.engine.url import make_url

    url = make_url(settings.DATABASE_URL)
    if "postgresql" in url.drivername and "+asyncpg" not in url.drivername:
        url = url.set(drivername="postgresql+asyncpg")

    engine = create_async_engine(url)
    async with engine.connect() as conn:
        print("Checking first 10 trips with fuel data...")
        res = await conn.execute(
            text(
                "SELECT id, tuketim, mesafe_km, is_real, ton FROM seferler WHERE tuketim > 0 LIMIT 10"
            )
        )
        for row in res:
            # row: (id, tuketim, mesafe_km, is_real, ton)
            print(
                f"ID: {row[0]}, FuelVal: {row[1]}, Dist: {row[2]}, Real: {row[3]}, Ton: {row[4]}"
            )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_fuel_values())
