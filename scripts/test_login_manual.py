import requests


def test_login():
    url = "http://localhost:8000/api/v1/auth/token"
    # Varsayılan admin credentials (genelde admin/admin veya admin/password oluyor, veya veritabanındaki bir kullanıcı)
    # Projedeki seed verisine göre admin:admin123 olabilir.
    payload = {
        "username": "admin",
        "password": "password",  # Eğer başarısız olursa diğer yaygın şifreleri deneriz
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    print(f"Testing Login: {url}")
    try:
        response = requests.post(url, data=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ Login Successful!")
            print(f"Token: {response.json().get('access_token')}")
        else:
            print("❌ Login Failed.")

    except Exception as e:
        print(f"❌ Connection Error: {e}")


if __name__ == "__main__":
    test_login()
