import asyncio
import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal
from app.core.ml.model_manager import get_model_manager, ModelType


async def debug_activation():
    print("Debugging Model Activation...")

    # 1. Dump Table
    async with AsyncSessionLocal() as session:
        print("\n--- Current Model Versions ---")
        result = await session.execute(
            text(
                "SELECT id, arac_id, version, model_type, is_active::text FROM model_versions"
            )
        )
        rows = result.fetchall()
        for row in rows:
            print(
                f"ID: {row.id}, Arac: {row.arac_id}, Ver: {row.version}, Type: {row.model_type}, Active: {row.is_active_text}"
            )

    # 2. Try Manual Activation
    print("\n--- Attempting Manual Activation ---")
    try:
        manager = get_model_manager()
        # Assume ID 1 exists (from previous training)
        # Find latest ID for arac 1
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT MAX(id) FROM model_versions WHERE arac_id=1")
            )
            latest_id = result.scalar()

        if latest_id:
            print(f"Activating Version ID: {latest_id}")
            success = manager.activate_version(latest_id)
            print(f"Activation Result: {success}")
        else:
            print("No version found to activate.")

    except Exception as e:
        print(f"Exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_activation())
