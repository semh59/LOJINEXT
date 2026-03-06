import sys
import os
import asyncio
from sqlalchemy import text
import json
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import get_sync_session
from app.infrastructure.routing.openroute_client import get_route_client
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


def verify_persistence():
    print("Starting persistence verification...")

    dummy_id = None
    client = get_route_client()
    # Refresh key just in case
    client.api_key = os.getenv("OPENROUTE_API_KEY")
    if not client.api_key:
        print("ERROR: API Key still missing!")
        return

    try:
        # 1. Insert Dummy Location
        with get_sync_session() as session:
            print("Inserting dummy location...")
            result = session.execute(
                text("""
                INSERT INTO lokasyonlar (cikis_yeri, varis_yeri, mesafe_km, cikis_lat, cikis_lon, varis_lat, varis_lon, zorluk, flat_distance_km)
                VALUES ('Test Origin', 'Test Dest', 100, 40.7669, 29.4319, 39.9334, 32.8597, 'Normal', 0)
                RETURNING id;
            """)
            )
            dummy_id = result.scalar()
            session.commit()
            print(f"Dummy location inserted with ID: {dummy_id}")

        # 2. Update Route Distance (triggers API and Save)
        print("Updating route distance (calling API)...")
        # Ensure API key is set
        from dotenv import load_dotenv

        load_dotenv()

        # We need to ensure update_route_distance uses include_details=True internally?
        # Wait, OpenRouteClient.update_route_distance hardcodes the call to get_distance?
        # Let's check the code.
        # It calls: result = self.get_distance(origin, destination, use_cache=False)
        # It defaults include_details=False in get_distance signature!
        # So update_route_distance needs to be updated to pass include_details=True!

        # I need to check OpenRouteClient again.
        if dummy_id:
            result = client.update_route_distance(dummy_id)
            print(f"Update Result: {result}")

            # Verify Persistence
            with get_sync_session() as session:
                row = session.execute(
                    text("SELECT route_analysis FROM lokasyonlar WHERE id=:id"),
                    {"id": dummy_id},
                ).fetchone()
                if row and row.route_analysis:
                    print(
                        f"SUCCESS: route_analysis saved: {str(row.route_analysis)[:100]}..."
                    )
                else:
                    print("FAILED: route_analysis is NULL or empty.")

    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        # 3. Clean up
        if dummy_id:
            with get_sync_session() as session:
                print(f"Cleaning up dummy location ID: {dummy_id}")
                session.execute(
                    text("DELETE FROM lokasyonlar WHERE id = :id"), {"id": dummy_id}
                )
                session.commit()


if __name__ == "__main__":
    verify_persistence()
