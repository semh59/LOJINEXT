"""
Backend Structure Check Script.

Import ve kritik bağımlılıkları doğrular.
"""

import sys
import os
from pathlib import Path

# Add project root to path (doğru şekilde)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.infrastructure.verification.verify_utils import VerificationRunner


def main():
    runner = VerificationRunner(
        "Backend Structure Check", 
        "Validates imports and critical dependencies"
    )
    
    # Register checks
    runner.register_check("app")
    runner.register_check("xgboost")
    runner.register_check("asyncpg")
    runner.register_check("sqlalchemy")
    runner.register_check("pydantic")

    # App Import Check
    if runner.should_run_check("app"):
        try:
            from app.main import app
            runner.add_result("App Import", True, "FastAPI app imported successfully.")
        except Exception as e:
            runner.add_result("App Import", False, f"Failed to import app: {str(e)}")

    # XGBoost Check
    if runner.should_run_check("xgboost"):
        try:
            import xgboost
            runner.add_result("XGBoost", True, f"XGBoost available (v{xgboost.__version__}).")
        except ImportError:
            runner.add_result("XGBoost", True, "XGBoost not installed (Optional).")

    # asyncpg Check
    if runner.should_run_check("asyncpg"):
        try:
            import asyncpg
            runner.add_result("asyncpg", True, "asyncpg available.")
        except ImportError:
            runner.add_result("asyncpg", False, "asyncpg missing - async DB desteği çalışmaz.")

    # SQLAlchemy Check
    if runner.should_run_check("sqlalchemy"):
        try:
            import sqlalchemy
            runner.add_result("SQLAlchemy", True, f"SQLAlchemy v{sqlalchemy.__version__}")
        except ImportError:
            runner.add_result("SQLAlchemy", False, "SQLAlchemy missing - kritik bağımlılık!")

    # Pydantic Check  
    if runner.should_run_check("pydantic"):
        try:
            import pydantic
            is_v2 = hasattr(pydantic, 'VERSION') and pydantic.VERSION.startswith('2')
            runner.add_result(
                "Pydantic", 
                True, 
                f"Pydantic v{pydantic.VERSION} ({'v2' if is_v2 else 'v1'})"
            )
        except ImportError:
            runner.add_result("Pydantic", False, "Pydantic missing - kritik bağımlılık!")

    runner.finalize()


if __name__ == "__main__":
    main()
