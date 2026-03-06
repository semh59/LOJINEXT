import requests

BASE_URL = "http://localhost:8000/api/v1"


# 1. Login as Super Admin to setup test data
def get_admin_token():
    print("Logging in as Super Admin...")
    response = requests.post(
        f"{BASE_URL}/auth/token", data={"username": "skara", "password": "!23efe25ali!"}
    )
    if response.status_code != 200:
        print(f"FAILED to login as Admin: {response.status_code}, {response.text}")
        return None
    return response.json()["access_token"]


# 2. Check if test user exists, otherwise create or just use one if possible
def create_test_user(admin_token):
    print("Checking/Creating test user...")
    # Since I don't want to mess up user table太多, I'll just check if I can register/create
    # Note: app/api/v1/endpoints/users.py usually has user creation.
    # We will try to create 'test_driver' with role 'user'
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "email": "test_sofor_ahmet@lojinext.com",
        "sifre": "Sofor123!",
        "ad_soyad": "Ahmet Sofor",
        "rol_id": 2,  # Assuming 2 is 'user' role
        "sofor_id": 58,
    }
    # Attempt to create (might fail if exists, which is fine)
    response = requests.post(f"{BASE_URL}/users/", headers=headers, json=payload)
    if response.status_code == 200 or response.status_code == 201:
        print("Test user created successfully.")
    elif response.status_code == 400:
        print("Test user already exists or error.")
    else:
        print(f"Unexpected status creating user: {response.status_code}")


def test_vulnerabilities():
    admin_token = get_admin_token()
    if not admin_token:
        return

    create_test_user(admin_token)

    # 3. Login as Restricted User
    print("\nLogging in as Restricted User (Ahmet)...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": "test_sofor_ahmet", "password": "Sofor123!"},
    )
    user_token = response.json().get("access_token")
    if not user_token:
        print("FAILED to login as user.")
        return

    headers_user = {"Authorization": f"Bearer {user_token}"}

    # 4. TEST: Data Isolation - Can user see ONLY their trips?
    print("\n[TEST 1] Data Isolation check (GET /trips)...")
    response = requests.get(f"{BASE_URL}/trips/", headers=headers_user)
    if response.status_code == 200:
        trips = response.json()
        print(f"RESULT: USER saw {len(trips)} trips.")
        # Verifying that ALL returned trips belong to the user (sofor_id=58)
        # Note: in real API, we might not return sofor_id in SeferResponse if not Admin,
        # but here we can check if total count is restricted.
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        total_trips = len(
            requests.get(f"{BASE_URL}/trips/", headers=headers_admin).json()
        )
        print(f"DEBUG: System has total {total_trips} trips.")

        if len(trips) < total_trips and len(trips) > 0:
            print("✅ SUCCESS: Data is isolated! Restricted user saw a subset of data.")
        elif len(trips) == total_trips and total_trips > 1:
            print("⚠️ VULNERABILITY: Restricted user can see ALL trips in the system!")
        else:
            print("ℹ️ Isolation check inconclusive (possible only 1 trip exists total).")
    else:
        print(f"FAILED to list trips: {response.status_code}")

    # 5. TEST: Unauthorized Access to specific Trip ID
    print("\n[TEST 2] Access specific Trip ID (Unauthorized ID check)...")
    # Get first trip ID from any admin list
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    admin_trips = requests.get(f"{BASE_URL}/trips/", headers=headers_admin).json()
    if admin_trips:
        target_id = admin_trips[0]["id"]
        print(f"Attempting to read Trip ID {target_id} as restricted user...")
        response = requests.get(f"{BASE_URL}/trips/{target_id}", headers=headers_user)
        if response.status_code == 200:
            print(
                f"⚠️ VULNERABILITY: User can read details of Trip {target_id} which might not belong to them!"
            )
        else:
            print(
                f"✅ Access to specific ID denied/filtered with {response.status_code}"
            )

    # 6. TEST: Forbidden Action (Delete)
    print("\n[TEST 3] Forbidden Action (DELETE trip)...")
    if admin_trips:
        target_id = admin_trips[0]["id"]
        response = requests.delete(
            f"{BASE_URL}/trips/{target_id}", headers=headers_user
        )
        if response.status_code == 403:
            print("✅ Authorization SUCCESS: User cannot delete trip (403 Forbidden).")
        elif response.status_code == 200:
            print("🚨 CRITICAL VULNERABILITY: Regular user DELETED a trip!")
        else:
            print(f"System returned {response.status_code} on delete.")

    # 6. TEST: Sensitive Data Leak (Password Hash)
    print("\n[TEST 4] Sensitive Data Leak (Password Hash check)...")
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/users/", headers=headers_admin)
    if response.status_code == 200:
        content = response.text
        if "sifre_hash" in content or "password" in content.lower():
            print("⚠️ VULNERABILITY: Sensitive password data found in API response!")
        else:
            print("✅ SUCCESS: No sensitive password data found in User list.")
    else:
        print(f"FAILED to list users: {response.status_code}")


if __name__ == "__main__":
    test_vulnerabilities()
