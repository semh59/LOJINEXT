import sys
import os
import json

sys.path.append(os.getcwd())
from app.database.connection import SyncSessionLocal
from app.database.models import Lokasyon


def diagnose_highway(route_id):
    db = SyncSessionLocal()
    try:
        r = db.get(Lokasyon, route_id)
        if r:
            print(f"ROUTE {r.id}: {r.cikis_yeri} -> {r.varis_yeri}")
            if r.route_analysis:
                print("ROUTE ANALYSIS JSON:")
                print(json.dumps(r.route_analysis, indent=2))
            else:
                print("route_analysis IS EMPTY/NULL")
        else:
            print("Route not found")
    finally:
        db.close()


if __name__ == "__main__":
    diagnose_highway(4)
