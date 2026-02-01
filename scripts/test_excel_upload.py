import httpx
import asyncio
import pandas as pd
import io

async def test_excel_upload():
    # 1. Create dynamic Excel file with new columns
    df = pd.DataFrame([
        {
            "Plaka": "34TEST99",
            "Marka": "TestTIR", 
            "Model": "X1000",
            "Yil": 2024,
            "Tank_Kapasitesi": 900,
            "Bos_Agirlik_KG": 8500,
            "Motor_Verimliligi": 0.42  # New column test
        },
        {
            "Plaka": "34ABC123", # Duplicate test
            "Marka": "Mercedes", 
            "Model": "Actros",
            "Yil": 2023, 
            "Tank_Kapasitesi": 600,
            "Bos_Agirlik_KG": 8000,
            "Motor_Verimliligi": 0.38
        }
    ])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    files = {'file': ('test_araclar.xlsx', output, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Authenticate
        login_res = await client.post(
            "http://localhost:8000/api/v1/auth/token",
            data={"username": "skara", "password": "!23efe25ali!"}
        )
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload
        print("Uploading generated Excel file...")
        res = await client.post(
            "http://localhost:8000/api/v1/vehicles/upload",
            files=files,
            headers=headers
        )
        
        print(f"Upload Status: {res.status_code}")
        print(f"Response: {res.text}")

        if res.status_code == 200:
             # Verify data created correctly
             res_get = await client.get(
                 "http://localhost:8000/api/v1/vehicles/?search=34TEST99",
                 headers=headers
             )
             print(f"Verification Get: {res_get.text}")

if __name__ == "__main__":
    asyncio.run(test_excel_upload())
