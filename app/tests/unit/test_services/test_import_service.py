"""
Unit Tests - ImportService
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.services.import_service import ImportService


class TestResolveIds:
    """ID resolution tests for ImportService (Plaka and Name matching)"""

    @pytest.fixture
    def service(self):
        # Tüm bağımlılıkları mock'la ki gerçek servisler/repo'lar çağrılmasın (hang/takılma önleme)
        return ImportService(
            arac_repo=MagicMock(),
            sofor_repo=MagicMock(),
            sefer_service=MagicMock(),
            yakit_service=MagicMock(),
            arac_service=MagicMock(),
            sofor_service=MagicMock()
        )

    @pytest.fixture
    def sample_data(self):
        return {
            'vehicles': [
                {'id': 1, 'plaka': '34 ABC 123', 'marka': 'Mercedes'},
                {'id': 2, 'plaka': '06 XYZ 456', 'marka': 'Volvo'},
                {'id': 3, 'plaka': '16TIR789', 'marka': 'Scania'},
            ],
            'drivers': [
                {'id': 1, 'ad_soyad': 'Ahmet Yılmaz'},
                {'id': 2, 'ad_soyad': 'Mehmet Kara'},
            ]
        }

    def test_resolve_arac_id_variants(self, service, sample_data):
        """Plaka matching with different formats"""
        vehicles = sample_data['vehicles']
        assert service._resolve_arac_id('34 ABC 123', vehicles) == 1
        assert service._resolve_arac_id('34ABC123', vehicles) == 1
        assert service._resolve_arac_id('34  abc   123', vehicles) == 1
        assert service._resolve_arac_id('16 TIR 789', vehicles) == 3

    def test_resolve_arac_id_not_found(self, service, sample_data):
        """Vehicle not found error"""
        with pytest.raises(ValueError, match="Araç bulunamadı"):
            service._resolve_arac_id('00 ZZZ 000', sample_data['vehicles'])

    def test_resolve_sofor_id_variants(self, service, sample_data):
        """Driver name matching variants"""
        drivers = sample_data['drivers']
        assert service._resolve_sofor_id('Ahmet Yılmaz', drivers) == 1
        assert service._resolve_sofor_id('ahmet yılmaz', drivers) == 1
        assert service._resolve_sofor_id('  Ahmet Yılmaz  ', drivers) == 1

    def test_resolve_sofor_id_not_found(self, service, sample_data):
        """Driver not found error"""
        with pytest.raises(ValueError, match="Şoför bulunamadı"):
            service._resolve_sofor_id('Bilinmeyen', sample_data['drivers'])


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

        # Mock repos (Async)
        mock_arac_repo.get_all = AsyncMock(return_value=[{'id': 1, 'plaka': '34 ABC 123', 'marka': 'Mercedes'}])
        mock_sofor_repo.get_all = AsyncMock(return_value=[{'id': 1, 'ad_soyad': 'Ahmet Yılmaz'}])
        
        # Mock services (Async)
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
            sofor_service=mock_sofor_service
        )

    @patch('app.core.services.import_service.ExcelService')
    @pytest.mark.asyncio
    async def test_process_sefer_import_valid(self, MockExcelService, service):
        """Valid trip import flow"""
        MockExcelService.parse_sefer_excel = AsyncMock(return_value=[
            {
                'plaka': '34 ABC 123',
                'sofor_adi': 'Ahmet Yılmaz',
                'tarih': date.today(),
                'cikis_yeri': 'Ankara',
                'varis_yeri': 'İstanbul',
                'mesafe_km': 450,
                'net_kg': 20000
            }
        ])

        count, errors = await service.process_sefer_import(b'fake')
        assert count == 1
        assert len(errors) == 0
        service.sefer_service.bulk_add_sefer.assert_called_once()

    @patch('app.core.services.import_service.ExcelService')
    @pytest.mark.asyncio
    async def test_process_sefer_import_invalid_vehicle(self, MockExcelService, service):
        """Trip import with unknown vehicle"""
        MockExcelService.parse_sefer_excel = AsyncMock(return_value=[{'plaka': '00X'}])
        
        count, errors = await service.process_sefer_import(b'fake')
        assert count == 0
        assert any("Araç bulunamadı" in error for error in errors)

    @patch('app.core.services.import_service.ExcelService')
    @pytest.mark.asyncio
    async def test_process_yakit_import_valid(self, MockExcelService, service):
        """Valid fuel import flow"""
        MockExcelService.parse_yakit_excel = AsyncMock(return_value=[
            {
                'plaka': '34 ABC 123',
                'tarih': date.today(),
                'istasyon': 'Shell',
                'litre': 500,
                'fiyat_tl': 45.0,
                'km_sayac': 150000
            }
        ])

        count, errors = await service.process_yakit_import(b'fake')
        assert count == 1
        assert len(errors) == 0
        service.yakit_service.bulk_add_yakit.assert_called_once()

    @patch('app.core.services.import_service.ExcelService')
    @pytest.mark.asyncio
    async def test_process_vehicle_import_valid(self, MockExcelService, service):
        """Valid vehicle import flow"""
        # Note: parse_vehicle_data is also async in production
        MockExcelService.parse_vehicle_data = AsyncMock(return_value=[
            {
                'plaka': '06 XYZ 456',
                'marka': 'Volvo',
                'model': 'FH16',
                'yil': 2022,
                'tank_kapasitesi': 800
            }
        ])

        count, errors = await service.process_vehicle_import(b'fake')
        assert count == 1
        assert len(errors) == 0
        service.arac_service.bulk_add_arac.assert_called_once()

    @patch('app.core.services.import_service.ExcelService')
    @pytest.mark.asyncio
    async def test_process_vehicle_import_duplicate(self, MockExcelService, service):
        """Vehicle import with duplicate plate (should skip)"""
        MockExcelService.parse_vehicle_data = AsyncMock(return_value=[
            {'plaka': '34 ABC 123', 'marka': 'Mercedes'} # Duplicate
        ])
        
        count, errors = await service.process_vehicle_import(b'fake')
        assert count == 0
        assert any("zaten kayıtlı" in error for error in errors)

    @patch('app.core.services.import_service.ExcelService')
    @pytest.mark.asyncio
    async def test_process_driver_import_valid(self, MockExcelService, service):
        """Valid driver import flow"""
        MockExcelService.parse_driver_data = AsyncMock(return_value=[
            {
                'ad_soyad': 'Mehmet Kara',
                'telefon': '5550000000',
                'ehliyet_sinifi': 'CE'
            }
        ])

        count, errors = await service.process_driver_import(b'fake')
        assert count == 1
        assert len(errors) == 0
        service.sofor_service.bulk_add_sofor.assert_called_once()
