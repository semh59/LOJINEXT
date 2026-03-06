import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "skara"
PASSWORD = "!23efe25ali!"


def get_token():
    try:
        url = f"{BASE_URL}/auth/token"
        data = {"username": USERNAME, "password": PASSWORD}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Login Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return None


def check_endpoint(name, url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # If list, expect empty list
            if isinstance(data, list):
                if len(data) == 0:
                    print(f"✅ {name}: OK (Empty List)")
                else:
                    print(
                        f"⚠️ {name}: OK (Items found: {len(data)}) - Normal if seeded."
                    )
            # If paginated response
            elif isinstance(data, dict) and "items" in data:
                if len(data["items"]) == 0:
                    print(f"✅ {name}: OK (Empty Page)")
                else:
                    print(f"⚠️ {name}: OK (Items found: {len(data['items'])})")
            else:
                print(f"✅ {name}: OK (Status 200)")
            return True
        else:
            print(f"❌ {name}: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: Error ({e})")
        return False


def main():
    print("Testing Cold Start Resilience (Authenticated)...")

    # 0. Health Check
    check_endpoint("Root (Health)", "http://localhost:8000/")

    # Login
    print("Authenticating...")
    token = get_token()
    if not token:
        print("❌ Authentication failed. Aborting protected checks.")
        return

    # 1. Trips
    check_endpoint("Trips List", f"{BASE_URL}/trips?skip=0&limit=10", token)

    # 2. Fuel Records
    check_endpoint("Fuel Records", f"{BASE_URL}/fuel?skip=0&limit=10", token)

    # 3. Vehicles
    check_endpoint("Vehicles", f"{BASE_URL}/vehicles", token)

    # 4. Drivers
    check_endpoint("Drivers", f"{BASE_URL}/drivers", token)

    # 5. Dashboard Stats (via WebSocket or specific endpoint if any)
    # Skipping generic stats for now, lists are sufficient proof.


if __name__ == "__main__":
    main()
