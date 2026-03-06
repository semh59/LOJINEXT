import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.getcwd()))

from sqlalchemy import text
from app.database.connection import engine


async def verify_db():
    print("--- LOJINEXT DB INTEGRITY CHECK ---")

    tables_to_check = [
        "roller",
        "kullanicilar",
        "kullanici_oturumlari",
        "admin_audit_log",
        "sistem_konfig",
        "konfig_gecmis",
        "model_versiyonlar",
    ]

    async with engine.connect() as conn:
        # Check tables
        for table in tables_to_check:
            result = await conn.execute(
                text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                )
            )
            exists = result.scalar()
            status = "[OK]" if exists else "[FAIL]"
            print(f"{status} Table: {table}")

        print("\n--- SEED DATA CHECK ---")
        # Check SistemKonfig keys
        result = await conn.execute(text("SELECT anahtar FROM sistem_konfig"))
        keys = result.scalars().all()
        print(f"SistemKonfig keys: {list(keys)}")

        expected_groups = ["physics", "anomaly", "ml"]
        for group in expected_groups:
            result = await conn.execute(
                text(f"SELECT count(*) FROM sistem_konfig WHERE grup = '{group}'")
            )
            count = result.scalar()
            status = "[OK]" if count > 0 else "[FAIL]"
            print(f"{status} Group '{group}' has {count} entries")

        # Check Roller
        result = await conn.execute(text("SELECT count(*) FROM roller"))
        role_count = result.scalar()
        print(f"Role count: {role_count}")


if __name__ == "__main__":
    asyncio.run(verify_db())
