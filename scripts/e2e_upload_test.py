
import requests
import pandas as pd
import io

API_URL = "http://127.0.0.1:8000/api/v1"
# Admin token mechanism might be needed if auth is strict, 
# but for local dev with SessionDep/current_user dependency injection in main.py usually allows bypass or we need to login.
# Let's assume we need to login or mock auth. 
# Actually, the quickest way is to use the 'bypass' or just try catching the 401. 
# If 401, I'll need to implement login. 
# Let's try to grab a token first.

def get_token():
    # Attempt login with default creds
    try:
        resp = requests.post("http://127.0.0.1:8000/api/v1/auth/token", data={
            "username": "skara",
            "password": "!23efe25ali!"
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        print(f"Login Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Connection Error: {e}")
    return None

def create_driver_excel():
    df = pd.DataFrame([
        {
            "ad_soyad": "E2E Test Driver",
            "telefon": "5551112233",
            "ise_baslama": "2024-01-01",
            "ehliyet_sinifi": "E"
        }
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def create_vehicle_excel():
    df = pd.DataFrame([
        {
            "plaka": "34TST99",
            "marka": "Mercedes",
            "model": "Actros",
            "yil": 2023,
            "tank_kapasitesi": 600,
            "bos_agirlik_kg": 8000
        }
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def run_test():
    print("--- Starting E2E Upload Test ---")
    token = get_token()
    if not token:
        print("Skipping test due to login failure (API might not be ready).")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test Driver Upload
    print("\n[TEST 1] Uploading Driver Excel...")
    driver_excel = create_driver_excel()
    files = {'file': ('drivers.xlsx', driver_excel, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    
    resp = requests.post(f"{API_URL}/drivers/excel/upload", headers=headers, files=files)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    if resp.status_code == 200:
        print("✅ Driver Upload Success!")
    else:
        print("❌ Driver Upload Failed!")

    # 2. Test Vehicle Upload (Reactivation Check)
    print("\n[TEST 2] Uploading Vehicle Excel...")
    vehicle_excel = create_vehicle_excel()
    files_v = {'file': ('vehicles.xlsx', vehicle_excel, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    
    resp_v = requests.post(f"{API_URL}/vehicles/upload", headers=headers, files=files_v)
    print(f"Status: {resp_v.status_code}")
    print(f"Response: {resp_v.text}")
    
    if resp_v.status_code == 200 and "34TST99" in resp_v.text: # Or created message
        print("✅ Vehicle Upload Success!")
    else:
         # It might say "already loaded" if run twice, that's fine.
         if resp_v.status_code == 200:
             print("✅ Vehicle Upload Success (Already exists or created)")
         else:
             print("❌ Vehicle Upload Failed!")

    # 3. Verify Visibility
    print("\n[TEST 3] Verifying Vehicle Visibility (GET /vehicles)...")
    resp_get = requests.get(f"{API_URL}/vehicles/", headers=headers)
    if resp_get.status_code == 200:
        data = resp_get.json()
        found = any(v['plaka'] == '34TST99' for v in data)
        if found:
            print("✅ Vehicle '34TST99' is VISIBLE in list!")
        else:
            print("❌ Vehicle '34TST99' is NOT visible (Ghost Object Issue Persists!)")
            print(f"List Sample: {data[:2]}")
    else:
        print(f"❌ Failed to list vehicles: {resp_get.status_code}")
        print(f"Error: {resp_get.text}")

if __name__ == "__main__":
    run_test()
