import sys
import os

# Add root to python path to emulate running as module
sys.path.append(os.getcwd())

try:
    from app.services.route_service import get_route_service
    print("IMPORT_SUCCESS")
except ImportError as e:
    print(f"IMPORT_FAILED: {e}")
except Exception as e:
    print(f"OTHER_ERROR: {e}")
