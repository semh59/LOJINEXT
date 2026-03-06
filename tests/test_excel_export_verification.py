
import pytest
import pandas as pd
import io
from app.core.services.excel_service import ExcelService

class TestExcelExportEngine:
    """Excel Export Engine Verification Tests"""

    def test_export_data_generates_bytes(self):
        """Test that export_data returns bytes"""
        data = [{"col1": "val1", "col2": 123}]
        result = ExcelService.export_data(data, type="test")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_data_content_integrity(self):
        """Test that exported data matches input when read back"""
        input_data = [
            {"ad_soyad": "Ahmet Yilmaz", "puan": 1.5, "tarih": "2024-01-01"},
            {"ad_soyad": "Mehmet Demir", "puan": 0.8, "tarih": "2024-01-02"}
        ]
        
        # Generates Excel file in memory
        excel_bytes = ExcelService.export_data(input_data, type="integrity_check")
        
        # Read back with pandas
        # Note: export_data writes header at row 1 (0-indexed) -> row 2 in Excel
        # And adds a title at row 0.
        # So header is at index 1.
        df = pd.read_excel(io.BytesIO(excel_bytes), header=1)
        
        # Verify columns (Title Case and space replaced)
        assert "Ad Soyad" in df.columns
        assert "Puan" in df.columns
        assert "Tarih" in df.columns
        
        # Verify values
        assert df.iloc[0]["Ad Soyad"] == "Ahmet Yilmaz"
        assert df.iloc[0]["Puan"] == 1.5
        # Date might be read as string or timestamp depending on pandas
        # input was string "2024-01-01", expected in cell.
        assert "2024-01-01" in str(df.iloc[0]["Tarih"])

    def test_empty_data_handling(self):
        """Test export with empty list"""
        result = ExcelService.export_data([], type="empty")
        assert isinstance(result, bytes)
        # Should still have a valid excel structure
        df = pd.read_excel(io.BytesIO(result))
        assert df.empty

    def test_styling_header_exists(self):
        """Test that the title row is present"""
        data = [{"a": 1}]
        excel_bytes = ExcelService.export_data(data, type="styling_test")
        
        # Read without header to check first row (Title)
        df = pd.read_excel(io.BytesIO(excel_bytes), header=None)
        title_cell = df.iloc[0, 0]
        assert "STYLING_TEST RAPORU" in str(title_cell)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
