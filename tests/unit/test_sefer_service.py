import pytest
from unittest.mock import AsyncMock, patch
from datetime import date, timedelta
from pydantic import ValidationError
from app.core.services.sefer_service import SeferService
from app.core.entities.models import SeferCreate


class TestSeferService:
    @pytest.fixture
    def mock_uow(self):
        uow = AsyncMock()
        uow.__aenter__.return_value = uow
        uow.__aexit__.return_value = None

        # Mock Repositories
        uow.sefer_repo = AsyncMock()
        uow.sefer_repo.create.return_value = 1

        # Relation Objects
        active_arac = {"id": 1, "aktif": True, "plaka": "34ABC123"}
        active_sofor = {"id": 1, "aktif": True, "ad_soyad": "Test Driver"}
        active_guzergah = {
            "id": 1,
            "adi": "Route 1",
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450.0,
        }

        # Mock Arace & Sofor
        uow.arac_repo = AsyncMock()
        uow.arac_repo.get_by_id.return_value = active_arac

        uow.sofor_repo = AsyncMock()
        uow.sofor_repo.get_by_id.return_value = active_sofor

        # Mock Lokasyon/Guzergah
        # Service uses uow.session.get(Lokasyon) AND uow.lokasyon_repo.get_by_id

        uow.session = AsyncMock()
        uow.session.get.return_value = active_guzergah

        uow.lokasyon_repo = AsyncMock()
        uow.lokasyon_repo.get_by_id.return_value = active_guzergah

        # If code uses guzergah_repo, mock it too just in case
        uow.guzergah_repo = AsyncMock()
        uow.guzergah_repo.get_by_id.return_value = active_guzergah

        # Mock Prediction Service to avoid external calls
        # (Though we mock it separately via patch usually, let's see)

        return uow

    @pytest.fixture
    def mock_event_bus(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_event_bus):
        return SeferService(event_bus=mock_event_bus)

    @pytest.mark.asyncio
    async def test_add_sefer_valid(self, service, mock_uow):
        """Valid sefer creation should succeed"""
        sefer_data = SeferCreate(
            tarih=date.today(),
            arac_id=1,
            sofor_id=1,
            guzergah_id=1,
            cikis_yeri="Istanbul",
            varis_yeri="Ankara",
            mesafe_km=450.0,
            net_kg=25000,
            durum="Tamam",
            bos_sefer=False,
        )

        with (
            patch(
                "app.core.services.sefer_write_service.UnitOfWork",
                return_value=mock_uow,
            ),
            patch(
                "app.core.services.sefer_write_service.RouteValidator.validate_and_correct",
                side_effect=lambda x: x,
            ),
        ):
            result = await service.add_sefer(sefer_data)

        assert result == 1
        mock_uow.sefer_repo.add.assert_called_once()  # Helper method calls repo.add
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_sefer_same_locations(self, service, mock_uow):
        """Should raise ValueError if start and end locations are the same (Business Logic)"""
        sefer_data = SeferCreate(
            tarih=date.today(),
            arac_id=1,
            sofor_id=1,
            guzergah_id=1,
            cikis_yeri="Istanbul",
            varis_yeri="Istanbul",  # Valid for Pydantic (strings), invalid for Service
            mesafe_km=10.0,
            net_kg=1000,
            bos_sefer=False,
        )

        with patch(
            "app.core.services.sefer_write_service.UnitOfWork", return_value=mock_uow
        ):
            with pytest.raises(ValueError, match="aynı olamaz"):
                await service.add_sefer(sefer_data)

    def test_add_sefer_invalid_distance_pydantic(self):
        """Should raise ValidationError for zero or negative distance (Pydantic)"""
        with pytest.raises(ValidationError) as excinfo:
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                guzergah_id=1,
                cikis_yeri="LocA",
                varis_yeri="LocB",
                mesafe_km=0,  # Invalid
                net_kg=1000,
                bos_sefer=False,
            )
        assert "mesafe_km" in str(excinfo.value)

    def test_add_sefer_invalid_weight_pydantic(self):
        """Should raise ValidationError for negative weight (Pydantic)"""
        with pytest.raises(ValidationError) as excinfo:
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                guzergah_id=1,
                cikis_yeri="LocA",
                varis_yeri="LocB",
                mesafe_km=100,
                net_kg=-50,  # Invalid
                bos_sefer=False,
            )
        assert "net_kg" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_add_sefer_future_date_limit(self, service, mock_uow):
        """Should raise ValueError if date is too far in the future (Service Logic)"""
        future_date = date.today() + timedelta(days=366)
        sefer_data = SeferCreate(
            tarih=future_date,
            arac_id=1,
            sofor_id=1,
            guzergah_id=1,
            cikis_yeri="LocA",
            varis_yeri="LocB",
            mesafe_km=100,
            net_kg=1000,
            bos_sefer=False,
        )

        with patch(
            "app.core.services.sefer_write_service.UnitOfWork", return_value=mock_uow
        ):
            # Regex relaxed to match actual error message
            with pytest.raises(ValueError, match="ileri bir tarih olamaz"):
                await service.add_sefer(sefer_data)

    @pytest.mark.asyncio
    async def test_add_sefer_duplicate_sefer_no(self, service, mock_uow):
        """Should raise ValueError if sefer_no is already in use"""
        sefer_data = SeferCreate(
            tarih=date.today(),
            arac_id=1,
            sofor_id=1,
            guzergah_id=1,
            cikis_yeri="Istanbul",
            varis_yeri="Ankara",
            mesafe_km=450.0,
            net_kg=25000,
            sefer_no="DUPE-123",
        )

        # Mock existing sefer with same no
        mock_uow.sefer_repo.get_by_sefer_no.return_value = {
            "id": 100,
            "sefer_no": "DUPE-123",
        }

        with patch(
            "app.core.services.sefer_write_service.UnitOfWork", return_value=mock_uow
        ):
            with pytest.raises(ValueError, match="zaten kullanımda"):
                await service.add_sefer(sefer_data)

    @pytest.mark.asyncio
    async def test_create_return_trip_success(self, service, mock_uow):
        """Should successfully create a return trip with reversed locations and '-D' sefer_no"""
        # Setup mock reference trip
        mock_ref_sefer = {
            "id": 1,
            "arac_id": 1,
            "sofor_id": 1,
            "dorse_id": None,
            "guzergah_id": 1,
            "sefer_no": "TEST-001",
            "cikis_yeri": "Istanbul",
            "varis_yeri": "Ankara",
            "mesafe_km": 450.0,
            "bos_agirlik_kg": 15000,
            "ascent_m": 500,
            "descent_m": 300,
            "flat_distance_km": 200,
            "is_real": True,
        }
        mock_uow.sefer_repo.get_by_id.return_value = mock_ref_sefer

        with (
            patch(
                "app.core.services.sefer_write_service.UnitOfWork",
                return_value=mock_uow,
            ),
            patch(
                "app.core.services.sefer_write_service.RouteValidator.validate_and_correct",
                side_effect=lambda x: x,
            ),
        ):
            # Act
            result = await service.create_return_trip(sefer_id=1)

            # Assert
            assert result == 1  # ID of created trip

            # Check if add method was called with correctly reversed data
            add_call_args = mock_uow.sefer_repo.add.call_args[0][0]

            # Reversals check
            assert add_call_args.get("cikis_yeri") == "Ankara"
            assert add_call_args.get("varis_yeri") == "Istanbul"
            assert add_call_args.get("ascent_m") == 300
            assert add_call_args.get("descent_m") == 500

            # Sefer no check
            assert add_call_args.get("sefer_no") == "TEST-001-D"

            # Bos sefer check
            assert add_call_args.get("bos_sefer") is True
            assert add_call_args.get("net_kg") == 0

    @pytest.mark.asyncio
    async def test_create_return_trip_duplicate_d(self, service, mock_uow):
        """Should not create '-D-D' if original already had '-D'"""
        mock_ref_sefer = {
            "id": 2,
            "sefer_no": "TEST-001-D",
            "cikis_yeri": "Ankara",
            "varis_yeri": "Istanbul",
            "mesafe_km": 450.0,
            "arac_id": 1,
            "sofor_id": 1,
        }
        mock_uow.sefer_repo.get_by_id.return_value = mock_ref_sefer

        with (
            patch(
                "app.core.services.sefer_write_service.get_uow", return_value=mock_uow
            ),
            patch(
                "app.core.services.sefer_write_service.RouteValidator.validate_and_correct",
                side_effect=lambda x: x,
            ),
        ):
            await service.create_return_trip(sefer_id=2)
            add_call_args = mock_uow.sefer_repo.add.call_args[0][0]
            assert add_call_args.get("sefer_no") == "TEST-001-D"
