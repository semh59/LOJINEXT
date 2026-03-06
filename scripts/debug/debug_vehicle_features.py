import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/token"
VEHICLES_URL = f"{BASE_URL}/vehicles"

def get_token():
    """Get admin token"""
    payload = {
        "username": "admin",
        "password": "!23efe25ali!"
    }
    try:
        response = requests.post(LOGIN_URL, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        sys.exit(1)

def test_search(token):
    """Test search functionality (expecting failure initially)"""
    print("\n--- Testing Search ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. List all
    resp = requests.get(f"{VEHICLES_URL}/", headers=headers)
    all_vehicles = resp.json()
    print(f"Total vehicles: {len(all_vehicles)}")
    
    if not all_vehicles:
        print("No vehicles to search.")
        return None

    target_plate = all_vehicles[0]['plaka']
    print(f"Searching for plate: {target_plate}")

    # 2. Search
    params = {"search": target_plate}
    resp = requests.get(f"{VEHICLES_URL}/", headers=headers, params=params)
    
    if resp.status_code == 200:
        results = resp.json()
        print(f"Search results count: {len(results)}")
        # Check if filtering actually happened
        if len(results) < len(all_vehicles):
            print("✅ SUCCESS: Search worked (results filtered).")
        elif len(results) == 1 and results[0]['plaka'] == target_plate:
             print("✅ SUCCESS: Search worked (found exact match).")
        else:
             print(f"⚠️ UNDETERMINED: Got {len(results)} results.")
    else:
        print(f"❌ Search request failed: {resp.status_code}")
    
    return all_vehicles[0]['id']

def test_trailing_slashes(token, vehicle_id):
    """Test Update/Delete WITHOUT trailing slashes (Frontend Fix Verification)"""
    print("\n--- Testing Correct URLs (No Trailing Slashes) ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    if not vehicle_id:
        print("Skipping Update/Delete tests (no vehicle ID).")
        return

    # 1. Update WITHOUT trailing slash
    print(f"Attempting PUT {VEHICLES_URL}/{vehicle_id} (NO SLASH)")
    update_data = {"model_yili": 2024}
    
    # Allow redirects to see what happens, but log history
    resp = requests.put(f"{VEHICLES_URL}/{vehicle_id}", headers=headers, json=update_data, allow_redirects=True)
    
    print(f"Response Code: {resp.status_code}")
    if resp.history:
        print("Redirect History:")
        for r in resp.history:
            print(f"  {r.status_code} {r.url}")
    else:
        print("  No redirects (GOOD)")
    
    if resp.status_code == 200:
        print("✅ SUCCESS: Update without trailing slash worked.")
    else:
        print(f"❌ FAILURE: {resp.status_code} {resp.text}")

    # 2. Delete WITHOUT trailing slash
    # Create a dummy vehicle first to delete
    print("\nCreating dummy vehicle for delete test...")
    import random
    rnd = random.randint(1000, 9999)
    dummy_plaka = f"99 TST {rnd}"
    
    dummy_data = {
        "plaka": dummy_plaka,
        "marka": "Test",
        "model": "Test",
        "yil": 2023,
        "arac_tipi": "TIR",
        "yakit_tipi": "Dizel",
        "depo_kapasitesi": 500,
        "kullanim_amaci": "Lojistik",
        "varsayilan_sofor_id": None,
         # Adding required fields based on schema
        "on_kesit_alani_m2": 10.0,
        "hava_direnc_katsayisi": 0.5,
        "yuvarlanma_firen_katsayisi": 0.01,
        "motor_verimliligi": 0.4,
        "aktarma_verimliligi": 0.9,
        "motor_gucu_kw": 300,
        "agirlik_bos_ton": 15,
        "hedef_tuketim": 30.0
    }
    
    # Initial Create check (Standard creates at collection root /vehicles/)
    create_resp = requests.post(f"{VEHICLES_URL}/", headers=headers, json=dummy_data)
    
    if create_resp.status_code in [200, 201]:
        dummy_id = create_resp.json()['id']
        print(f"Created dummy vehicle {dummy_id}")
        
        # 1. First Delete -> Soft Delete
        print(f"Attempting SOFT DELETE {VEHICLES_URL}/{dummy_id}")
        del_resp = requests.delete(f"{VEHICLES_URL}/{dummy_id}", headers=headers)
        
        if del_resp.status_code == 200:
            print("✅ SUCCESS: Soft delete worked.")
            # Verify it's not in active list
            list_resp = requests.get(f"{VEHICLES_URL}/", headers=headers)
            active_ids = [v['id'] for v in list_resp.json()]
            if dummy_id not in active_ids:
                 print("✅ VERIFIED: Vehicle removed from active list.")
            else:
                 print("❌ FAILURE: Deleted vehicle still in active list.")

            # Check state explicitly
            mid_check = requests.get(f"{VEHICLES_URL}/{dummy_id}", headers=headers)
            if mid_check.status_code == 200:
                print(f"DEBUG: Vehicle State after Soft Delete: Aktif={mid_check.json().get('aktif')}")
            else:
                 print(f"DEBUG: Could not fetch vehicle after soft delete: {mid_check.status_code}")

            # 2. Second Delete -> Hard Delete (Smart Delete Feature)
            # Need to access it again. Standard get /vehicles/1 should still work if we implemented it right?
            # actually read_arac checks if not arac. logic doesn't filter by active.
            
            print(f"Attempting HARD DELETE (Passive->Gone) {VEHICLES_URL}/{dummy_id}")
            hard_del_resp = requests.delete(f"{VEHICLES_URL}/{dummy_id}", headers=headers)
            
            print(f"Hard Delete Headers: {hard_del_resp.headers}")

            if hard_del_resp.status_code == 200:
                print("✅ SUCCESS: Hard delete worked.")
                # Verify it's GONE from DB
                check_resp = requests.get(f"{VEHICLES_URL}/{dummy_id}", headers=headers)
                if check_resp.status_code == 404:
                    print("✅ VERIFIED: Vehicle permanently deleted (404).")
                else:
                    print(f"❌ FAILURE: Vehicle still exists with status {check_resp.status_code}")
            else:
                print(f"❌ FAILURE: Hard delete failed {hard_del_resp.status_code} {hard_del_resp.text}")

        else:
            print(f"❌ FAILURE: Soft delete failed {del_resp.status_code}")
    else:
        print(f"Skipping delete test, could not create dummy vehicle. {create_resp.status_code} {create_resp.text}")

if __name__ == "__main__":
    token = get_token()
    print("Got Admin Token.")
    vid = test_search(token)
    test_trailing_slashes(token, vid)
