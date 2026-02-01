"""
TIR Yakıt Takip - Business Flow Integration Tests
Kapsamlı iş akışı entegrasyon testleri. (Async Pytest Version)
"""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.entities import SeferCreate, YakitAlimiCreate

@pytest.mark.asyncio
async def test_end_to_end_flow(
    db_session,
    arac_repo,
    sefer_repo,
    yakit_repo
):
    """E2E Entegrasyon Testi - Manuel Injection ile Full İzolasyon"""
    from app.core.services.sefer_service import SeferService
    from app.core.services.yakit_service import YakitService
    from app.core.services.report_service import ReportService
    from app.core.services.analiz_service import AnalizService
    from app.database.repositories.sofor_repo import get_sofor_repo

    # Explicit Dependency Injection
    # Repos provided as fixtures are already bound to db_session in conftest.py
    # We create a local sofor_repo just for this test
    sofor_repo_local = get_sofor_repo(session=db_session)
    
    sefer_service = SeferService(repo=sefer_repo)
    yakit_service = YakitService(repo=yakit_repo)
    report_service = ReportService(
        sefer_repo=sefer_repo, 
        yakit_repo=yakit_repo, 
        arac_repo=arac_repo, 
        sofor_repo=sofor_repo_local
    )
    analiz_service = AnalizService(
        yakit_repo=yakit_repo, 
        sefer_repo=sefer_repo, 
        arac_repo=arac_repo
    )

    # --- PHASE 1: Filo Ops ---
    arac_id = await arac_repo.create(
        plaka="34 FLOW 01", marka="Mercedes", model="Actros", yil=2023, aktif=True
    )
    assert arac_id is not None

    sofor_id = await sofor_repo_local.create(ad_soyad="Flow Şoförü", telefon="555-1234")
    assert sofor_id is not None

    # Sefer ekleme
    sefer1_id = await sefer_service.add_sefer(SeferCreate(
        tarih=date.today(), arac_id=arac_id, sofor_id=sofor_id,
        cikis_yeri="İstanbul", varis_yeri="Ankara", mesafe_km=450, net_kg=20000
    ))

    sefer2_id = await sefer_service.add_sefer(SeferCreate(
        tarih=date.today() + timedelta(days=1), arac_id=arac_id, sofor_id=sofor_id,
        cikis_yeri="Ankara", varis_yeri="İstanbul", mesafe_km=450, net_kg=0, bos_sefer=True
    ))

    stats = await sofor_repo_local.get_sefer_stats(sofor_id=sofor_id)
    assert len(stats) > 0
    assert stats[0]['toplam_sefer'] == 2

    # --- PHASE 2: Yakıt & Analiz ---
    arac2_id = await arac_repo.create(plaka="06 FUEL 99", marka="Volvo", yil=2022, aktif=True)

    # Arac 2 için sefer ekle (Analiz için gerekli - filo ortalaması hesaplansın diye)
    await sefer_service.add_sefer(SeferCreate(
        tarih=date.today() - timedelta(days=2),
        arac_id=arac2_id,
        sofor_id=sofor_id,
        cikis_yeri="Ankara",
        varis_yeri="Bursa",
        mesafe_km=600,
        net_kg=15000
    ))

    await yakit_service.add_yakit(YakitAlimiCreate(
        tarih=date.today() - timedelta(days=5), arac_id=arac2_id,
        istasyon="İstasyon A", fiyat_tl=Decimal("40.0"), litre=500.0,
        km_sayac=100000,
        depo_durumu="Full"
    ))

    await yakit_service.add_yakit(YakitAlimiCreate(
        tarih=date.today(), arac_id=arac2_id,
        istasyon="İstasyon B", fiyat_tl=Decimal("42.0"), litre=180.0,
        km_sayac=100600,
        depo_durumu="Full"
    ))

    await analiz_service.recalculate_vehicle_periods(arac2_id)

    periods_db = await yakit_repo.get_fuel_periods(arac2_id)

    if len(periods_db) > 0:
        p = periods_db[0]
        assert p['ara_mesafe'] == 600
        assert p['toplam_yakit'] == 180.0
        assert abs(p['ort_tuketim'] - 30.0) < 0.1

    # --- PHASE 3: Dashboard ---
    summary = await report_service.get_dashboard_summary()
    assert summary.get('aktif_arac', 0) >= 2
    assert summary.get('filo_ortalama', 0) > 0

    trend = await report_service.get_daily_consumption_trend(days=7)
    assert summary is not None, "Dashboard summary döndürülemedi"
    assert isinstance(trend, list), "Trend bir liste olmalı"
