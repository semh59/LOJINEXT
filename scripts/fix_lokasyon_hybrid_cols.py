import asyncio
import os
import sys
from sqlalchemy import text
from app.database.connection import AsyncSessionLocal


async def main():
    print("--- Lojinext Database Migration: Lokasyonlar Schema Fix ---")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Check if columns exist (safety check)
            check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'lokasyonlar' 
            AND column_name IN ('source', 'is_corrected', 'correction_reason');
            """
            result = await session.execute(text(check_sql))
            existing_cols = [row[0] for row in result.fetchall()]
            print(f"Existing hybrid columns: {existing_cols}")

            # 2. Add source column if missing
            if "source" not in existing_cols:
                print("Adding 'source' column...")
                await session.execute(
                    text("ALTER TABLE lokasyonlar ADD COLUMN source VARCHAR(50);")
                )

            # 3. Add is_corrected column if missing
            if "is_corrected" not in existing_cols:
                print("Adding 'is_corrected' column...")
                await session.execute(
                    text(
                        "ALTER TABLE lokasyonlar ADD COLUMN is_corrected BOOLEAN DEFAULT FALSE;"
                    )
                )

            # 4. Add correction_reason column if missing
            if "correction_reason" not in existing_cols:
                print("Adding 'correction_reason' column...")
                await session.execute(
                    text("ALTER TABLE lokasyonlar ADD COLUMN correction_reason TEXT;")
                )

            # 5. Set default values for existing records
            print("Updating existing records with default values...")
            await session.execute(
                text(
                    "UPDATE lokasyonlar SET is_corrected = FALSE WHERE is_corrected IS NULL;"
                )
            )
            await session.execute(
                text("UPDATE lokasyonlar SET source = 'legacy' WHERE source IS NULL;")
            )

            await session.commit()
            print("Migration completed successfully.")

        except Exception as e:
            await session.rollback()
            print(f"Error during migration: {e}")
            sys.exit(1)


if __name__ == "__main__":
    # Ensure PYTHONPATH includes the current directory
    sys.path.append(os.getcwd())
    asyncio.run(main())
