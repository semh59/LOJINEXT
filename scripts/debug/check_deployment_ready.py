import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def check_env_vars():
    """Checks for required environment variables."""
    load_dotenv()
    required_vars = ["DATABASE_URL", "OPENROUTESERVICE_API_KEY", "SECRET_KEY"]
    missing_vars = []

    print("Checking environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
            print(f"  [OK] {var} is set ({masked})")

    if missing_vars:
        print(f"  [ERROR] Missing environment variables: {', '.join(missing_vars)}")
        return False
    return True


def check_db_connection():
    """Checks database connectivity."""
    print("\nChecking database connection...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("  [SKIP] DATABASE_URL not set.")
        return False

    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("  [OK] Database connection successful.")
        return True
    except Exception as e:
        print(f"  [ERROR] Database connection failed: {e}")
        return False


def main():
    print("Starting Deployment Readiness Check...\n")

    env_ok = check_env_vars()
    db_ok = check_db_connection()

    if env_ok and db_ok:
        print("\n[SUCCESS] System appears ready for deployment preparation.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Please fix the issues above before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    main()
