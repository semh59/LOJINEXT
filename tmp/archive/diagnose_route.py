import sys
import os

sys.path.append(os.getcwd())
from app.database.connection import SyncSessionLocal
from app.database.models import Lokasyon
from sqlalchemy import select


def diagnose_route(route_id):
    db = SyncSessionLocal()
    try:
        r = db.get(Lokasyon, route_id)
        if r:
            print(f"ROUTE {r.id}: {r.cikis_yeri} -> {r.varis_yeri}")
            print(f"  Mesafe: {r.mesafe_km}")
            print(f"  Ascent: {r.ascent_m}")
            print(f"  Descent: {r.descent_m}")
            print(
                f"  Rota Detay Valid: {bool(r.route_analysis)}"
            )  # models.py uses route_analysis, not rota_detay
        else:
            print("Route not found")
    finally:
        db.close()


if __name__ == "__main__":
    diagnose_route(4)
