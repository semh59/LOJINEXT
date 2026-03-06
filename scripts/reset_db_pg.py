import os
import subprocess
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuration
# Using sync driver for the script (psycopg2 or similar must be installed, usually implicit with sqlalchemy/asyncpg setup for tools sometimes)
# If asyncpg is the only one, we might need a sync driver string.
# Changing +asyncpg to +psycopg2 or just postgresql:// for standard lib if available.
# Assuming standard postgresql:// for execution if system has it.
# Or better, let's try to use the one from env but strip asyncpg if needed or rely on 'pg_dump' and 'psql' if available?
# No, let's use sqlalchemy.
DATABASE_URL = "postgresql://postgres:!23efe25ali!@localhost:5432/tir_yakit"


def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f"lojinext_backup_{timestamp}.sql")

    print(f"Creating backup at {backup_file}...")
    # Using pg_dump. Requires pg_dump in PATH.
    # PGPASSWORD environment variable can be used.
    env = os.environ.copy()
    env["PGPASSWORD"] = "!23efe25ali!"

    try:
        # Command: pg_dump -h localhost -U postgres -d tir_yakit -f backup_file
        cmd = [
            "pg_dump",
            "-h",
            "localhost",
            "-U",
            "postgres",
            "-d",
            "tir_yakit",
            "-f",
            backup_file,
        ]
        subprocess.run(cmd, env=env, check=True)
        print("✅ Backup successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e}")
        # Proceed with caution or exit? For now exit.
        exit(1)
    except FileNotFoundError:
        print("⚠ pg_dump not found in PATH. Skipping backup (RISKY).")


def reset_database():
    print("Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            print(
                "⚠ WARNING: This will TRUNCATE tables: seferler, yakit_alimlari, anomalies."
            )

            # Backup
            backup_database()

            print("Truncating tables...")
            # Using CASCADE to handle foreign keys
            conn.execute(
                text("TRUNCATE TABLE anomalies, yakit_alimlari, seferler CASCADE;")
            )

            conn.commit()
            print("✅ Database reset successful.")

            # Verify
            trips = conn.execute(text("SELECT COUNT(*) FROM seferler")).scalar()
            fuel = conn.execute(text("SELECT COUNT(*) FROM yakit_alimlari")).scalar()

            print(f"Stats -> Trips: {trips}, Fuel: {fuel}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    reset_database()
