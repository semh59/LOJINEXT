
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
        return None
    except:
        return None

def run_test():
    print("--- Testing Hard Delete ---")
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Ensure driver exists and is passive
    # Search for "Ghost Driver Test"
    resp = requests.get(f"{API_URL}/drivers/?search=Ghost Driver Test&aktif_only=false", headers=headers)
    found = [d for d in resp.json() if d['ad_soyad'] == "Ghost Driver Test"]
    
    if not found:
        print("Driver not found for delete test. creating...")
        requests.post(f"{API_URL}/drivers/", json={"ad_soyad": "Ghost Driver Test"}, headers=headers)
        # Fetch again
        resp = requests.get(f"{API_URL}/drivers/?search=Ghost Driver Test&aktif_only=false", headers=headers)
        found = [d for d in resp.json() if d['ad_soyad'] == "Ghost Driver Test"]

    if found:
        driver = found[0]
        print(f"Target: ID {driver['id']}, status: {driver['aktif']}")
        
        # If Active -> Delete (Soft)
        if driver['aktif']:
            print("Soft deleting...")
            requests.delete(f"{API_URL}/drivers/{driver['id']}", headers=headers)
            print("Soft deleted.")
            
        # Verify it is passive
        # Now HARD DELETE
        print("Executing Hard Delete (Passive -> None)...")
        resp_del = requests.delete(f"{API_URL}/drivers/{driver['id']}", headers=headers)
        
        print(f"Delete Status: {resp_del.status_code}")
        print(f"Response: {resp_del.text}")
        
        if resp_del.status_code == 200 and "tamamen silindi" in resp_del.text:
            print("✅ SUCCESS: Hard Delete Confirmed")
        else:
            print("❌ FAILURE: Could not hard delete")

if __name__ == "__main__":
    run_test()
