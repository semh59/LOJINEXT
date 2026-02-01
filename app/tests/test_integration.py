from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.entities import YakitAlimiCreate


@pytest.fixture
async def test_arac_id(arac_service):
    """Test için geçici araç oluştur"""
    from app.core.entities import AracCreate
    arac_id = await arac_service.create_arac(AracCreate(
        plaka="34 TEST 01",
        marka="Mercedes",
        model="Test",
        yil=2023,
        aktif=True
    ))
    return arac_id

@pytest.mark.asyncio
async def test_yakit_ekleme_basarili(yakit_service, yakit_repo, test_arac_id):
    """Doğru veriyle yakıt ekleme testi"""
    dto = YakitAlimiCreate(
        tarih=date.today(),
        arac_id=test_arac_id,
        istasyon="Test Petrol",
        fiyat_tl=Decimal("40.50"),
        litre=100.0,
        km_sayac=50100
    )

    y_id = await yakit_service.add_yakit(dto)

    # DB'den oku ve doğrula
    # Repo üzerinden okuyoruz
    from app.database.repositories.yakit_repo import get_yakit_repo
    # yakit_repo fixture yoksa get_yakit_repo kullanalim veya conftest'e ekleyelim
    # conftest'te yoktu, service vardi.
    # Service uzerinden get_by_id yok mu? Yoksa repo kullanalim.
    repo = get_yakit_repo()
    kayit = await repo.get_by_id(y_id)

    assert kayit is not None
    assert kayit["litre"] == 100.0
    assert float(kayit["fiyat_tl"]) * float(kayit["litre"]) == 4050.0  # 40.50 * 100
    assert kayit["durum"] == "Bekliyor"

@pytest.mark.asyncio
async def test_hatali_veri_engelleme(yakit_service, test_arac_id):
    """Negatif değerlerin engellenmesi testi"""

    # Negatif litre - Model validasyonu sırasında hata fırlatmalı
    with pytest.raises(ValidationError):
        YakitAlimiCreate(
            tarih=date.today(),
            arac_id=test_arac_id,
            fiyat_tl=Decimal("40.0"),
            litre=-10,  # HATA: gt=0 kuralı
            km_sayac=50000
        )

    # DB'ye yazılmadığını doğrula (Service çağrılmadı bile)
    from app.database.repositories.yakit_repo import get_yakit_repo
    repo = get_yakit_repo()
    kayitlar = await repo.get_all(test_arac_id)
    assert len(kayitlar) == 0

@pytest.mark.asyncio
async def test_update_islemi(yakit_service, test_arac_id):
    """Güncelleme testi"""
    # Önce ekle
    dto = YakitAlimiCreate(
        tarih=date.today(),
        arac_id=test_arac_id,
        fiyat_tl=Decimal("40.0"),
        litre=50.0,
        km_sayac=10000
    )
    y_id = await yakit_service.add_yakit(dto)

    # Güncelle (Fiyat değişti)
    dto.fiyat_tl = Decimal("50.0")
    await yakit_service.update_yakit(y_id, dto)

    # Kontrol et
    from app.database.repositories.yakit_repo import get_yakit_repo
    repo = get_yakit_repo()
    kayit = await repo.get_by_id(y_id)

    assert float(kayit["fiyat_tl"]) == 50.0
    assert float(kayit["fiyat_tl"]) * float(kayit["litre"]) == 2500.0 # 50 * 50

@pytest.mark.asyncio
async def test_odometer_rollback_prevented(yakit_service, test_arac_id):
    """KM düşüşünün engellenmesi testi"""
    # 1. Kayıt
    await yakit_service.add_yakit(YakitAlimiCreate(
        tarih=date.today(), arac_id=test_arac_id,
        fiyat_tl=Decimal("40.0"), litre=50.0, km_sayac=50000
    ))

    # 2. Kayıt (Düşük KM) - Service Logic Hatası (ValueError)
    dto = YakitAlimiCreate(
        tarih=date.today(), arac_id=test_arac_id,
        fiyat_tl=Decimal("40.0"), litre=50.0, km_sayac=49000 # HATA
    )

    with pytest.raises(ValueError, match="KM Sayacı düşemez"):
        await yakit_service.add_yakit(dto)

@pytest.mark.asyncio
async def test_future_date_prevented(yakit_service, test_arac_id):
    """İleri tarihli giriş engeli"""
    future = date.today() + timedelta(days=1)

    dto = YakitAlimiCreate(
        tarih=future, arac_id=test_arac_id,
        fiyat_tl=Decimal("40.0"), litre=50.0, km_sayac=51000
    )
    # Service katmanında kontrol yapılmalı
    with pytest.raises(ValueError, match="İleri tarihli"):
        await yakit_service.add_yakit(dto)
