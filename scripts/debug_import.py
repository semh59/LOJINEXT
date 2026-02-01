import sys
from pathlib import Path
sys.path.append(r"d:\PROJECT\excel")

try:
    print("Importing SeferService...")
    from app.core.services.sefer_service import get_sefer_service
    print("Success")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
