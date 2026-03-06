import sys
import os
import asyncio
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import AsyncSessionLocal


async def cleanup_test_data():
    print("Starting Cleanup of Stress Test Data...")
    async with AsyncSessionLocal() as session:
        try:
            # The stress test created trips with "Stress Test" in notes
            # We can use that to identify and delete them safely.
            # Or we can delete by the IDs we saw in the logs (793, 794, 795)
            # But "Stress Test" finding is safer.

            # Check count first
            result = await session.execute(
                text("SELECT count(*) FROM seferler WHERE notlar LIKE 'Stress Test%'")
            )
            count = result.scalar()
            print(f"Found {count} test records to delete.")

            if count > 0:
                await session.execute(
                    text("DELETE FROM seferler WHERE notlar LIKE 'Stress Test%'")
                )
                await session.commit()
                print(f"Successfully deleted {count} records.")
            else:
                print("No records found to delete.")

        except Exception as e:
            await session.rollback()
            print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(cleanup_test_data())
