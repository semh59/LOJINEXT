import os
import sys

# Mock environment before importing settings
os.environ["ENVIRONMENT"] = "dev"
os.environ["SECRET_KEY"] = "dev_secret_key_change_me_in_prod"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:!23efe25ali!@localhost:5432/tir_yakit"
)
os.environ["OPENROUTESERVICE_API_KEY"] = "test_key"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://test.com"

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.config import Settings
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def test_cors_parsing():
    settings = Settings()
    expected = ["http://localhost:3000", "http://test.com"]
    if settings.CORS_ORIGINS == expected:
        print("[SUCCESS] CORS Parsing Test: PASSED")
    else:
        print(
            f"[FAILURE] CORS Parsing Test: FAILED. Expected {expected}, got {settings.CORS_ORIGINS}"
        )
        return False
    return True


def test_prod_wildcard_restriction():
    # Set to prod
    os.environ["ENVIRONMENT"] = "prod"
    # Overwrite CORS_ORIGINS to wildcard
    os.environ["CORS_ORIGINS"] = "*"
    try:
        Settings()
        print("[FAILURE] Prod Wildcard Test: FAILED (Should have raised ValueError)")
        return False
    except ValueError as e:
        if "SECURITY RISK" in str(e):
            print("[SUCCESS] Prod Wildcard Test: PASSED (Correctly blocked '*')")
        else:
            print(f"[FAILURE] Prod Wildcard Test: FAILED (Unexpected error: {e})")
            return False
    return True


if __name__ == "__main__":
    print("Starting CORS Verification (Config-only)...")
    res1 = test_cors_parsing()
    res2 = test_prod_wildcard_restriction()

    if res1 and res2:
        print("\nOVERALL STATUS: ALL TESTS PASSED")
    else:
        print("\nOVERALL STATUS: TESTS FAILED")
        sys.exit(1)
