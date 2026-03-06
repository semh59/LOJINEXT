
import requests

API_URL = "http://127.0.0.1:8000/api/v1"

def get_token():
    try:
        resp = requests.post(f"{API_URL}/auth/token", data={
            "username": "skara",
            "password": "!23efe25ali!"
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        print(f"Login Failed: {resp.status_code}")
        return None
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def run_test():
    print("--- Starting Driver Reactivation Test ---")
    token = get_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Driver (might exist)
    driver_data = {
        "ad_soyad": "Ghost Driver Test",
        "telefon": "5550009988",
        "ehliyet_sinifi": "E"
    }
    
    # Try creating. If exists (active), it raises 400.
    # If exists (passive), it should reactivate.
    
    # First, let's delete it to ensure state.
    # Get ID by name (search)
    resp_search = requests.get(f"{API_URL}/drivers/?search=Ghost Driver Test&aktif_only=false", headers=headers)
    if resp_search.status_code == 200:
        found = [d for d in resp_search.json() if d['ad_soyad'] == "Ghost Driver Test"]
        if found:
            print(f"Found existing driver ID: {found[0]['id']}, Active: {found[0]['aktif']}")
            # Delete it (to passive)
            if found[0]['aktif']:
                requests.delete(f"{API_URL}/drivers/{found[0]['id']}", headers=headers)
                print("Deleted (Soft) driver.")
    
    # NOW: Try to create it. It should be "Passive" in DB now.
    print("Attempting to CREATE driver (expecting Reactivation)...")
    resp_create = requests.post(f"{API_URL}/drivers/", json=driver_data, headers=headers)
    
    print(f"Create Status: {resp_create.status_code}")
    print(f"Create Body: {resp_create.text}")
    
    if resp_create.status_code == 200:
        print("✅ SUCCESS: Driver reactivated/created!")
        data = resp_create.json()
        print(f"Returned Data: {data}")
    else:
        print("❌ FAILURE: Could not create/reactivate driver.")

if __name__ == "__main__":
    run_test()
