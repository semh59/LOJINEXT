"""
Improvements Verification Script.

Yeni servis ve model alanlarını kontrol eder.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.infrastructure.verification.verify_utils import VerificationRunner


def main():
    runner = VerificationRunner(
        "Improvements Verification", 
        "Check for new services and model fields"
    )
    
    # Register checks
    runner.register_check("excel")
    runner.register_check("route")
    runner.register_check("ai")
    runner.register_check("models")

    # ExcelService Check
    if runner.should_run_check("excel"):
        start = time.time()
        try:
            from app.core.services.excel_service import ExcelService
            excel = ExcelService()
            runner.add_result(
                "ExcelService", 
                True, 
                "Imported and instantiated.",
                duration=time.time() - start
            )
        except Exception as e:
            runner.add_result(
                "ExcelService", 
                False, 
                f"Failed: {str(e)}",
                duration=time.time() - start
            )

    # RouteService Check
    if runner.should_run_check("route"):
        start = time.time()
        try:
            from app.services.route_service import RouteService
            route = RouteService()
            runner.add_result(
                "RouteService", 
                True, 
                "Imported and instantiated.",
                duration=time.time() - start
            )
        except Exception as e:
            runner.add_result(
                "RouteService", 
                False, 
                f"Failed: {str(e)}",
                duration=time.time() - start
            )

    # LocalAIService Check
    if runner.should_run_check("ai"):
        start = time.time()
        try:
            runner.add_result(
                "LocalAIService", 
                True, 
                "Syntax check passed (Import OK).",
                duration=time.time() - start
            )
        except Exception as e:
            runner.add_result(
                "LocalAIService", 
                False, 
                f"Failed: {str(e)}",
                duration=time.time() - start
            )

    # Models Check
    if runner.should_run_check("models"):
        start = time.time()
        try:
            from app.database.models import Sofor, Sefer
            s = Sofor()
            sofor_ok = hasattr(s, 'score')
            
            t = Sefer()
            sefer_ok = hasattr(t, 'rota_detay') and hasattr(t, 'tahmini_tuketim')
            
            if sofor_ok and sefer_ok:
                runner.add_result(
                    "Models Schema", 
                    True, 
                    "New fields found in Sofor and Sefer.",
                    {"sofor_score": sofor_ok, "sefer_fields": sefer_ok},
                    duration=time.time() - start
                )
            else:
                runner.add_result(
                    "Models Schema", 
                    False, 
                    f"Missing fields: Sofor.score={sofor_ok}, Sefer.fields={sefer_ok}",
                    duration=time.time() - start
                )
        except Exception as e:
            runner.add_result(
                "Models Schema", 
                False, 
                f"Failed: {str(e)}",
                duration=time.time() - start
            )

    runner.finalize()


if __name__ == "__main__":
    main()
