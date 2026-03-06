import asyncio
from sqlalchemy import text
from app.database.connection import engine
from app.config import settings


async def debug_db():
    print(f"Connecting to: {settings.DATABASE_URL}")
    async with engine.connect() as conn:
        # Check constraints for vehicle_event_log
        sql = """
        SELECT
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'vehicle_event_log';
        """
        result = await conn.execute(text(sql))
        rows = result.fetchall()
        print("\nConstraints for vehicle_event_log:")
        for row in rows:
            print(row)

        # Check triggers
        sql = "SELECT trigger_name, event_manipulation, event_object_table, action_statement FROM information_schema.triggers"
        result = await conn.execute(text(sql))
        rows = result.fetchall()
        print("\nTriggers:")
        for row in rows:
            print(row)


if __name__ == "__main__":
    asyncio.run(debug_db())
