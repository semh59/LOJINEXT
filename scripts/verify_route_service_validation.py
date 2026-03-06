import sys
import os
import asyncio
import json
from contextlib import asynccontextmanager
from sqlalchemy import text

sys.path.append(os.getcwd())

# Ensure env is loaded
from dotenv import load_dotenv

load_dotenv()

from app.services.route_service import RouteService
from app.database.connection import AsyncSessionLocal


@asynccontextmanager
async def get_async_session_ctx():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def verify_validation():
    print("Testing RouteService Validation (Cache Correction)...")

    # Coordinates for a dummy route
    lat1, lon1 = 40.0, 30.0
    lat2, lon2 = 41.0, 31.0
    dist_km = 100.0
    bad_ascent = 5000.0

    async with get_async_session_ctx() as session:
        # Check if exists, delete first
        await session.execute(
            text(
                "DELETE FROM route_paths WHERE origin_lat = :l1 AND origin_lon = :ln1"
            ),
            {"l1": lat1, "ln1": lon1},
        )
        await session.commit()

        # Insert
        print(f"Inserting BAD cache record: {dist_km}km, {bad_ascent}m ascent...")
        await session.execute(
            text("""
                INSERT INTO route_paths 
                (origin_lat, origin_lon, dest_lat, dest_lon, distance_km, duration_min, 
                 ascent_m, descent_m, flat_distance_km, geometry, fuel_estimate_cache, last_fetched)
                VALUES 
                (:l1, :ln1, :l2, :ln2, :dist, 60, :asc, 0, 0, :json, 'null', now())
            """),
            {
                "l1": lat1,
                "ln1": lon1,
                "l2": lat2,
                "ln2": lon2,
                "dist": dist_km,
                "asc": bad_ascent,
                "json": json.dumps({"type": "LineString", "coordinates": []}),
            },
        )
        await session.commit()

    # 2. Call Service
    service = RouteService()
    # Mocking get_uow().route_repo used in RouteService?
    # RouteService uses 'get_uow()' which is imported.
    # We rely on 'get_uow' working correctly in script context.
    # 'get_uow' usually needs DB setup.
    # 'app.database.unit_of_work' implementation:
    # It likely uses 'AsyncSessionLocal'.

    try:
        result = await service.get_route_details(
            (lon1, lat1), (lon2, lat2), use_cache=True
        )
    except Exception as e:
        print(f"Service Call Failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # 3. Validation
    print(f"Result Ascent: {result.get('ascent_m')}")

    if result.get("ascent_m") == 1500.0:
        print("SUCCESS: Anomalous data was corrected!")
    elif result.get("ascent_m") == 5000.0:
        print("FAIL: Data was NOT corrected.")
    else:
        print(f"UNKNOWN: {result.get('ascent_m')}")

    # Cleanup
    async with get_async_session_ctx() as session:
        await session.execute(
            text(
                "DELETE FROM route_paths WHERE origin_lat = :l1 AND origin_lon = :ln1"
            ),
            {"l1": lat1, "ln1": lon1},
        )
        await session.commit()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_validation())
