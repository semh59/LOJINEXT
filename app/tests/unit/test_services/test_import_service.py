"""
Unit Tests - ImportService
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.services.import_service import ImportService


class TestResolveIds:
    """ID resolution tests for ImportService (Plaka and Name matching)"""

    @pytest.fixture
    def service(self):
        return ImportService(
            arac_repo=MagicMock(),
            sofor_repo=MagicMock(),
            sefer_service=MagicMock(),
            yakit_service=MagicMock(),
            arac_service=MagicMock(),
            sofor_service=MagicMock(),
        )

    @pytest.fixture
    def sample_data(self):
        return {
            "vehicles": [
                {"id": 1, "plaka": "34 ABC 123", "marka": "Mercedes"},
                {"id": 2, "plaka": "06 XYZ 456", "marka": "Volvo"},
                {"id": 3, "plaka": "16TIR789", "marka": "Scania"},
            ],
            "drivers": [
                {"id": 1, "ad_soyad": "Ahmet Yılmaz"},
                {"id": 2, "ad_soyad": "Mehmet Kara"},
            ],
        }

    def test_resolve_arac_id_variants(self, service, sample_data):
        vehicles = sample_data["vehicles"]
        assert service._resolve_arac_id("34 ABC 123", vehicles) == 1
        assert service._resolve_arac_id("34ABC123", vehicles) == 1
        assert service._resolve_arac_id("34  abc   123", vehicles) == 1
        assert service._resolve_arac_id("16 TIR 789", vehicles) == 3

    def test_resolve_arac_id_not_found(self, service, sample_data):
        with pytest.raises(ValueError, match="Araç bulunamadı"):
            service._resolve_arac_id("00 ZZZ 000", sample_data["vehicles"])

    def test_resolve_sofor_id_variants(self, service, sample_data):
        drivers = sample_data["drivers"]
        assert service._resolve_sofor_id("Ahmet Yılmaz", drivers) == 1
        assert service._resolve_sofor_id("ahmet yılmaz", drivers) == 1

    def test_resolve_sofor_id_not_found(self, service, sample_data):
        with pytest.raises(ValueError, match="Şoför bulunamadı"):
            service._resolve_sofor_id("Bilinmeyen", sample_data["drivers"])


class TestProcessImports:
    """Import flow tests for ImportService (Async)"""

    @pytest.fixture
    def service(self):
        mock_arac_repo = MagicMock()
        mock_sofor_repo = MagicMock()
        mock_sefer_service = MagicMock()
        mock_yakit_service = MagicMock()
        mock_arac_service = MagicMock()
        mock_sofor_service = MagicMock()

        mock_arac_repo.get_all = AsyncMock(
            return_value=[
                {"id": 1, "plaka": "34 ABC 123", "marka": "Mercedes", "aktif": True}
            ]
        )
        mock_sofor_repo.get_all = AsyncMock(
            return_value=[{"id": 1, "ad_soyad": "Ahmet Yılmaz"}]
        )

        mock_sefer_service.bulk_add_sefer = AsyncMock(return_value=1)
        mock_yakit_service.bulk_add_yakit = AsyncMock(return_value=1)
        mock_arac_service.bulk_add_arac = AsyncMock(return_value=1)
        mock_sofor_service.bulk_add_sofor = AsyncMock(return_value=1)

        return ImportService(
            arac_repo=mock_arac_repo,
            sofor_repo=mock_sofor_repo,
            sefer_service=mock_sefer_service,
            yakit_service=mock_yakit_service,
            arac_service=mock_arac_service,
            sofor_service=mock_sofor_service,
        )

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_sefer_import_valid(self, MockExcelService, service):
        MockExcelService.parse_sefer_excel = AsyncMock(
            return_value=[
                {
                    "plaka": "34 ABC 123",
                    "sofor_adi": "Ahmet Yılmaz",
                    "tarih": date.today(),
                    "cikis_yeri": "Ankara",
                    "varis_yeri": "İstanbul",
                    "mesafe_km": 450,
                    "net_kg": 20000,
                }
            ]
        )
        count, errors = await service.process_sefer_import(b"fake")
        assert count == 1
        assert len(errors) == 0

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_yakit_import_valid(self, MockExcelService, service):
        MockExcelService.parse_yakit_excel = AsyncMock(
            return_value=[
                {
                    "plaka": "34 ABC 123",
                    "tarih": date.today(),
                    "istasyon": "Shell",
                    "litre": 500,
                    "fiyat_tl": 45.0,
                    "km_sayac": 150000,
                }
            ]
        )
        count, errors = await service.process_yakit_import(b"fake")
        assert count == 1
        assert len(errors) == 0

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_vehicle_import_valid(self, MockExcelService, service):
        MockExcelService.parse_vehicle_data = AsyncMock(
            return_value=[
                {
                    "plaka": "34 ADM 001",
                    "marka": "Mercedes",
                    "model": "Actros",
                    "yil": 2022,
                }
            ]
        )
        # Non-existing in DB
        service.arac_repo.get_all = AsyncMock(return_value=[])
        service.arac_service.bulk_add_arac = AsyncMock(return_value=1)

        count, errors = await service.process_vehicle_import(b"fake")
        assert count == 1
        assert len(errors) == 0

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_vehicle_import_reactivate(self, MockExcelService, service):
        MockExcelService.parse_vehicle_data = AsyncMock(
            return_value=[
                {"plaka": "34 ABC 123", "marka": "Mercedes", "model": "Actros"}
            ]
        )
        service.arac_repo.get_all = AsyncMock(
            return_value=[{"id": 1, "plaka": "34 ABC 123", "aktif": False}]
        )
        service.arac_repo.update = AsyncMock()
        service._arac_service = AsyncMock()
        service._arac_service.bulk_add_arac = AsyncMock(return_value=0)

        count, errors = await service.process_vehicle_import(b"fake")
        assert any("aktifleştirildi" in error for error in errors)
        service.arac_repo.update.assert_called_once()
        assert count == 0

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_driver_import_valid(self, MockExcelService, service):
        MockExcelService.parse_driver_data = AsyncMock(
            return_value=[{"ad_soyad": "Yeni Sofor", "telefon": "5551112233"}]
        )
        service.sofor_repo.get_all = AsyncMock(return_value=[])
        service.sofor_service.bulk_add_sofor = AsyncMock(return_value=1)

        count, errors = await service.process_driver_import(b"fake")
        assert count == 1
        assert len(errors) == 0

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_import_routes_valid(self, MockExcelService, service):
        MockExcelService.parse_route_excel = AsyncMock(
            return_value=[
                {"cikis_yeri": "Istanbul", "varis_yeri": "Ankara", "mesafe_km": 450.0}
            ]
        )
        # Use private attribute because it's a property
        service._guzergah_service = AsyncMock()
        service._guzergah_service.create_guzergah = AsyncMock(return_value=1)

        count, errors = await service.import_routes(b"fake")
        assert count == 1
        assert len(errors) == 0
        service._guzergah_service.create_guzergah.assert_called_once()

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_import_routes_empty(self, MockExcelService, service):
        """Test with empty route excel"""
        MockExcelService.parse_route_excel = AsyncMock(return_value=[])
        count, errors = await service.import_routes(b"fake")
        assert count == 0
        assert "boş" in errors[0]

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_sefer_import_empty(self, MockExcelService, service):
        """Test with empty trip excel"""
        MockExcelService.parse_sefer_excel = AsyncMock(return_value=[])
        count, errors = await service.process_sefer_import(b"fake")
        assert count == 0
        assert "veri bulunamadı" in errors[0]

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_yakit_import_empty(self, MockExcelService, service):
        """Test with empty fuel excel"""
        MockExcelService.parse_yakit_excel = AsyncMock(return_value=[])
        count, errors = await service.process_yakit_import(b"fake")
        assert count == 0
        assert "veri bulunamadı" in errors[0]

    @patch("app.core.services.import_service.ExcelService")
    @pytest.mark.asyncio
    async def test_process_sefer_import_error(self, MockExcelService, service):
        """Test system error during import"""
        MockExcelService.parse_sefer_excel.side_effect = Exception("Excel error")
        count, errors = await service.process_sefer_import(b"fake")
        assert count == 0
        assert "Sistem hatası" in errors[0]


class TestImportValidation:
    @pytest.fixture
    def service(self):
        return ImportService(
            MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()
        )

    def test_validate_plaka(self, service):
        assert service._validate_plaka("34 abc 123") == "34ABC123"
        with pytest.raises(ValueError, match="boş olamaz"):
            service._validate_plaka("")
        with pytest.raises(ValueError, match="uzunluğu"):
            service._validate_plaka("A")
        with pytest.raises(ValueError, match="formatı"):
            service._validate_plaka("ABCDEFG")

    def test_validate_name(self, service):
        assert service._validate_name("ahmet yılmaz") == "Ahmet Yılmaz"
        with pytest.raises(ValueError, match="en az 2"):
            service._validate_name("A")

    def test_validate_location(self, service):
        assert service._validate_location("İstanbul") == "İstanbul"

    def test_validate_numeric(self, service):
        assert service._validate_numeric("123.4", "Test") == 123.4
        with pytest.raises(ValueError, match="sayı olmalı"):
            service._validate_numeric("abc", "Test")


def test_get_import_service_singleton():
    from app.core.services.import_service import get_import_service

    with patch("app.core.container.get_container") as mock_cont:
        mock_instance = MagicMock()
        mock_cont.return_value.import_service = mock_instance
        svc = get_import_service()
        assert svc == mock_instance
