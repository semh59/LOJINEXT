"""
QT Startup Verification Script.

PyQt6 views'ların başlatılabilirliğini doğrular.
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path (doğru şekilde)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.infrastructure.verification.verify_utils import VerificationRunner


def main():
    runner = VerificationRunner(
        "QT Startup Verification", 
        "Validates QT Views initialization"
    )
    
    # Register checks
    runner.register_check("environment")
    runner.register_check("imports")
    runner.register_check("qapplication")
    runner.register_check("views")
    
    app = None  # QApplication referansı
    
    start = time.time()
    
    # Environment check
    if runner.should_run_check("environment"):
        # Headless check
        if sys.platform != "win32" and not os.environ.get("DISPLAY"):
            runner.add_result(
                "QT Environment", 
                True, 
                "Skipped: No DISPLAY found (likely CI/Headless).",
                {"headless": True},
                duration=time.time() - start
            )
            runner.finalize()
            return
        else:
            runner.add_result(
                "QT Environment",
                True,
                f"Platform: {sys.platform}, DISPLAY available",
                duration=time.time() - start
            )
    
    try:
        # Imports check
        if runner.should_run_check("imports"):
            start = time.time()
            try:
                from PyQt6.QtWidgets import QApplication
                from PyQt6.QtCore import QTimer
                
                from ui_qt.main import run_qt_app
                from ui_qt.views.dashboard_view import DashboardView
                from ui_qt.views.fuel_list_view import FuelListView
                from ui_qt.views.trip_list_view import TripListView
                from ui_qt.views.fuel_prediction_view import FuelPredictionView
                
                runner.add_result(
                    "Imports", 
                    True, 
                    "PyQt6 and Views imported successfully.",
                    duration=time.time() - start
                )
            except ImportError as e:
                runner.add_result(
                    "Imports",
                    False,
                    f"Import failed: {str(e)}",
                    duration=time.time() - start
                )
                runner.finalize()
                return
        
        # QApplication check
        if runner.should_run_check("qapplication"):
            start = time.time()
            try:
                from PyQt6.QtWidgets import QApplication
                app = QApplication(list(sys.argv))
                runner.add_result(
                    "QApplication", 
                    True, 
                    "QApplication created.",
                    duration=time.time() - start
                )
            except Exception as e:
                runner.add_result(
                    "QApplication",
                    False,
                    f"QApplication failed: {str(e)}",
                    duration=time.time() - start
                )
                runner.finalize()
                return
        
        # Views initialization check
        if runner.should_run_check("views"):
            start = time.time()
            try:
                from ui_qt.views.dashboard_view import DashboardView
                from ui_qt.views.fuel_list_view import FuelListView
                from ui_qt.views.trip_list_view import TripListView
                from ui_qt.views.fuel_prediction_view import FuelPredictionView
                
                # Instantiate views
                views = []
                dash = DashboardView()
                views.append(("DashboardView", dash))
                
                fuel = FuelListView()
                views.append(("FuelListView", fuel))
                
                trip = TripListView()
                views.append(("TripListView", trip))
                
                pred = FuelPredictionView()
                views.append(("FuelPredictionView", pred))
                
                runner.add_result(
                    "Views Init", 
                    True, 
                    f"All {len(views)} views initialized without errors.",
                    {"views": [v[0] for v in views]},
                    duration=time.time() - start
                )
                
                # Cleanup - view'ları kapat
                for name, view in views:
                    try:
                        view.close()
                        view.deleteLater()
                    except Exception:
                        pass
                        
            except Exception as e:
                runner.add_result(
                    "Views Init",
                    False,
                    f"View initialization failed: {str(e)}",
                    duration=time.time() - start
                )
                
    except Exception as e:
        runner.add_result(
            "QT Startup", 
            False, 
            f"Failed: {str(e)}", 
            duration=time.time() - start
        )
    finally:
        # QApplication cleanup
        if app:
            try:
                app.quit()
            except Exception:
                pass

    runner.finalize()


if __name__ == "__main__":
    main()
