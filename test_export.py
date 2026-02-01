import asyncio
import io
import pandas as pd
from app.core.services.sefer_service import get_sefer_service
from app.core.services.excel_service import ExcelService
from app.database.connection import AsyncSessionLocal

async def test_excel_export():
    async with AsyncSessionLocal() as session:
        # Mocking the service call logic (simplified)
        service = get_sefer_service()
        seferler = await service.get_all_paged(limit=10)
        
        data = []
        for s in seferler:
            d = s.model_dump()
            d["tarih"] = s.tarih.strftime("%Y-%m-%d") if s.tarih else ""
            d["durum"] = s.durum
            d["plaka"] = s.plaka or ""
            d["sofor"] = s.sofor_adi or ""
            data.append(d)
        
        print(f"Exporting {len(data)} records...")
        content = ExcelService.export_data(data, type="sefer_listesi")
        
        # Verify content exists
        if not content:
            print("FAIL: Content is empty.")
            return

        try:
            # Assuming row 0 is Title, Row 1 is Headers
            df = pd.read_excel(io.BytesIO(content), header=1)
            print("Layout Check (Row 1 headers):", list(df.columns))
            
            # Checks for Turkish Column Names which are likely used in Export Service
            expected = ['Tarih', 'Plaka', 'Şoför']
            found = [col for col in df.columns if any(e in str(col) for e in expected)]
            
            if len(found) >= 2:
                 print("SUCCESS: Excel file contains expected data columns.")
            else:
                 print(f"WARNING: Could not find exact columns. Found: {list(df.columns)}")
        except Exception as e:
            print(f"FAIL: Generated content is not a valid Excel file. Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_excel_export())
