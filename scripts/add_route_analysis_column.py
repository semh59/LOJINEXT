import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import get_sync_session
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


def migrate():
    print("Starting migration: Adding route_analysis column to lokasyonlar table...")

    try:
        with get_sync_session() as session:
            # Check if column exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='lokasyonlar' AND column_name='route_analysis';
            """)
            result = session.execute(check_query).fetchone()

            if result:
                print("Column 'route_analysis' already exists. Skipping.")
            else:
                # Add column
                alter_query = text(
                    "ALTER TABLE lokasyonlar ADD COLUMN route_analysis JSONB;"
                )
                session.execute(alter_query)
                session.commit()
                print("Successfully added 'route_analysis' column.")

    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
