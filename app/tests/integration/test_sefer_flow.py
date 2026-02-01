import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text

# Add project root
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.entities.models import SeferCreate, YakitAlimiCreate
from app.core.services.sefer_service import get_sefer_service
from app.core.services.yakit_service import get_yakit_service
from app.database.repositories.sefer_repo import get_sefer_repo


@pytest.mark.asyncio
async def test_create_and_retrieve_sefer(db_session):
    """Sefer oluştur ve geri oku"""
    sefer_service = get_sefer_service()
    sefer_repo = get_sefer_repo()

    # Setup Data
    arac_id = None
    sofor_id = None

    # db_session yields session, we use it directly
    await db_session.execute(text("""
        INSERT INTO araclar (plaka, marka, model, yil, aktif) 
        VALUES (:plaka, :marka, :model, :yil, :aktif)
    """), {"plaka": "99 TEST 01", "marka": "TestMarka", "model": "TestModel", "yil": 2024, "aktif": True})

    await db_session.execute(text("""
        INSERT INTO soforler (ad_soyad, telefon, ise_baslama, aktif, ehliyet_sinifi, score, hiz_disiplin_skoru, agresif_surus_faktoru) 
        VALUES (:ad, :tel, :tarih, :aktif, :ehliyet, :score, :hiz, :agresif)
    """), {"ad": "Test Şoför", "tel": "5551234567", "tarih": "2024-01-01", "aktif": True, "ehliyet": "E", "score": 1.0, "hiz": 1.0, "agresif": 1.0})

    arac_res = await db_session.execute(text("SELECT id FROM araclar WHERE plaka = '99 TEST 01'"))
    arac_id = arac_res.scalar()

    sofor_res = await db_session.execute(text("SELECT id FROM soforler WHERE telefon = '5551234567'"))
    sofor_id = sofor_res.scalar()

    await db_session.commit()

    # Sefer oluştur
    sefer_data = SeferCreate(
        tarih=date.today(),
        arac_id=arac_id,
        sofor_id=sofor_id,
        cikis_yeri="Ankara",
        varis_yeri="İstanbul",
        mesafe_km=450,
        net_kg=20000
    )

    sefer_id = await sefer_service.add_sefer(sefer_data)

    # Doğrula
    assert sefer_id is not None
    assert sefer_id > 0

    # Geri oku (Repo calls likely async now too)
    saved = await sefer_repo.get_by_id(sefer_id)
    assert saved is not None
    assert saved['cikis_yeri'] == 'Ankara'
    assert saved['varis_yeri'] == 'İstanbul'
    assert saved['mesafe_km'] == 450

@pytest.mark.asyncio
async def test_transaction_rollback_on_error(db_session):
    """Hata durumunda transaction rollback (Async test)"""
    # Service kullanılmıyor, sadece session.

    res_initial = await db_session.execute(text("SELECT COUNT(*) FROM araclar"))
    initial = res_initial.scalar()

    try:
        # Nested transaction for async session
        async with db_session.begin_nested():
            await db_session.execute(text("INSERT INTO araclar (plaka, marka, aktif) VALUES (:plaka, :marka, :aktif)"),
                           {"plaka": "99 ROLLBACK 01", "marka": "Test", "aktif": True})

            # İkinci insert (Unique Violation)
            await db_session.execute(text("INSERT INTO araclar (plaka, marka, aktif) VALUES (:plaka, :marka, :aktif)"),
                           {"plaka": "99 ROLLBACK 01", "marka": "Test", "aktif": True})
    except Exception:
        pass

    res_final = await db_session.execute(text("SELECT COUNT(*) FROM araclar"))
    final = res_final.scalar()

    assert initial == final, "Rollback çalışmadı!"

@pytest.mark.asyncio
async def test_add_and_verify_fuel(db_session):
    """Yakıt ekle ve kontrol et"""
    yakit_service = get_yakit_service()

    # Araç oluştur
    arac_id = None

    await db_session.execute(text("""
        INSERT INTO araclar (plaka, marka, model, yil, aktif) 
        VALUES (:plaka, :marka, :model, :yil, :aktif)
    """), {"plaka": "99 FUEL 01", "marka": "TestMarka", "model": "TestModel", "yil": 2024, "aktif": True})

    arac_res = await db_session.execute(text("SELECT id FROM araclar WHERE plaka = '99 FUEL 01'"))
    arac_id = arac_res.scalar()
    await db_session.commit()

    # Yakıt ekle
    yakit_data = YakitAlimiCreate(
        tarih=date.today(),
        arac_id=arac_id,
        istasyon="TestShell",
        litre=500,
        fiyat_tl=Decimal("45.0"),
        km_sayac=100000
    )

    yakit_id = await yakit_service.add_yakit(yakit_data)

    # Doğrula
    assert yakit_id is not None
    assert yakit_id > 0
