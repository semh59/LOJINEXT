import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.core.services.excel_service import ExcelService
import pandas as pd
import io


def verify_template():
    try:
        print("Verifying 'yakit' Excel template...")
        content = ExcelService.generate_template("yakit")
        print(f"Template generated: {len(content)} bytes")

        # Read back to verify headers
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        print(f"Headers found: {list(df.columns)}")

        expected_headers = [
            "Tarih",
            "Plaka",
            "İstasyon",
            "Fiyat",
            "Litre",
            "KM",
            "Fiş No",
            "Depo Durumu",
        ]
        for header in expected_headers:
            if header not in df.columns:
                print(f"MISSING HEADER: {header}")
            else:
                print(f"Header '{header}' OK")

        print("Template verification SUCCESSFULL.")

    except Exception as e:
        print(f"FAILED with error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    verify_template()
