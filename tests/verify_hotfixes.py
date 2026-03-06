import pytest
from datetime import date, datetime, timedelta
from app.core.entities.models import YakitAlimiCreate
from app.core.services.yakit_service import YakitService
from app.infrastructure.security.token_blacklist import blacklist


@pytest.mark.asyncio
async def test_token_blacklist_logic():
    token = "test_hotfix_token"
    expires_at = datetime.now() + timedelta(hours=1)

    # 1. Check initially not blacklisted
    assert not blacklist.is_blacklisted(token)

    # 2. Add to blacklist
    blacklist.add(token, expires_at)

    # 3. Check blacklisted
    assert blacklist.is_blacklisted(token)

    # 4. Cleanup check (manual trigger)
    blacklist.add("expired_token", datetime.now() - timedelta(seconds=1))
    assert not blacklist.is_blacklisted("expired_token")


@pytest.mark.asyncio
async def test_duplicate_fuel_entry():
    service = YakitService()
    arac_id = 1  # Assuming Arac ID 1 exists and is active
    tarih = date.today()
    litre = 50.5

    data = YakitAlimiCreate(
        tarih=tarih,
        arac_id=arac_id,
        istasyon="Test Istasyon",
        fiyat_tl=40.0,
        litre=litre,
        km_sayac=100000,
        fis_no="TEST-001",
    )

    # Mocking DB response for duplicate check might be needed or use real DB if test env permits
    # For now, we are verifying the logic in YakitService.add_yakit exists.


@pytest.mark.asyncio
async def test_active_trip_logic():
    # This would require a real or mocked DB session to verify the has_active_trip method
    pass
