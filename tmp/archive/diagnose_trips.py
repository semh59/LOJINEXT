import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database.connection import SyncSessionLocal
from app.database.models import Sefer
from sqlalchemy import select, desc


def diagnose():
    db = SyncSessionLocal()
    try:
        # Get last 5 trips
        stmt = select(Sefer).order_by(desc(Sefer.id)).limit(5)
        trips = db.execute(stmt).scalars().all()

        print(f"\n🔍 DIAGNOSIS REPORT: LAST {len(trips)} TRIPS\n" + "=" * 60)

        for t in trips:
            print(f"\n🆔 TRIP ID: {t.id} | SEFER NO: {t.sefer_no}")
            print(f"   📅 Tarih: {t.tarih}")
            print(f"   🚛 Araç ID: {t.arac_id} | Şoför ID: {t.sofor_id}")
            print(
                f"   📍 Rota: {t.cikis_yeri} -> {t.varis_yeri} (Güzergah ID: {t.guzergah_id})"
            )
            print(
                f"   ⚖️  Yük: {t.net_kg} kg ({t.net_kg / 1000 if t.net_kg else 0} Ton)"
            )
            print(f"   📏 Mesafe: {t.mesafe_km} km")
            print(f"   ❤️ Boş Sefer: {t.bos_sefer}")
            print(f"   🔮 Tahmin: {t.tahmini_tuketim} L")
            print(f"   ⛽ Gerçek: {t.tuketim} L")
            print(f"   📊 Durum: {t.durum}")
            # print(f"   📝 T/G Orani: {t.tahmin_gerceklesme_orani}") # Computed property might not work in sync session without eager load or hybrid property? Let's check model.
            print(f"   🗺️ Rota Detay: {bool(t.rota_detay)}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    diagnose()
