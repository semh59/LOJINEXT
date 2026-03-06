import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"


def test_trailers():
    print("Logging in...")
    try:
        login_res = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "skara", "password": "!23efe25ali!"},
        )
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return

        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        print("Testing GET /trailers/...")
        response = requests.get(f"{BASE_URL}/trailers/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_trailers()
