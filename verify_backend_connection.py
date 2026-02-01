
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_connection():
    try:
        print(f"Testing root connection to {BASE_URL}...")
        resp = requests.get(f"{BASE_URL}/")
        print(f"Root Status: {resp.status_code}")
        print(f"Root Response: {resp.text}")
        if resp.status_code != 200:
            print("FAILURE: Backend root not accessible")
            return
    except Exception as e:
        print(f"FAILURE: Connection error: {e}")
        return

    # Login
    print("\nAttempting Login (admin/admin123)...")
    try:
        login_resp = requests.post(
            f"{BASE_URL}/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login Status: {login_resp.status_code}")
        if login_resp.status_code != 200:
            print(f"FAILURE: Login failed. Response: {login_resp.text}")
            return
        
        token_data = login_resp.json()
        token = token_data.get("access_token")
        if not token:
            print("FAILURE: No access_token in response")
            return
        print(f"SUCCESS: Got token (prefix): {token[:10]}...")
    except Exception as e:
        print(f"FAILURE: Login exception: {e}")
        return

    # Verify Token (/me)
    print("\nAttempting /auth/me with token...")
    try:
        me_resp = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Me Status: {me_resp.status_code}")
        print(f"Me Response: {me_resp.text}")
        
        if me_resp.status_code == 200:
            print("SUCCESS: Full Auth Flow working via Script.")
        else:
            print("FAILURE: /me endpoint rejected token.")
    except Exception as e:
        print(f"FAILURE: /me request exception: {e}")

if __name__ == "__main__":
    test_connection()
