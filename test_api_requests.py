import requests


def main():
    login_data = {
        "username": "skara",
        "password": "!23efe25ali!",
        "grant_type": "password",
    }
    print("Testing Login...")
    res_login = requests.post(
        "http://127.0.0.1:8080/api/v1/auth/token", data=login_data
    )
    print("Login Status:", res_login.status_code)

    if res_login.status_code == 200:
        token = res_login.json().get("access_token")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print("\nTesting POST /api/v1/trailers/")
        payload = {
            "plaka": "34 TES 001",
            "marka": "Test Brand",
            "tipi": "Standart",
            "yil": 2024,
            "bos_agirlik_kg": 6000.0,
            "maks_yuk_kapasitesi_kg": 24000,
            "lastik_sayisi": 6,
            "aktif": True,
        }
        res_post = requests.post(
            "http://127.0.0.1:8080/api/v1/trailers/", json=payload, headers=headers
        )
        print("POST Status:", res_post.status_code)
        try:
            print("POST Response:", res_post.json())
        except:
            print("POST Response Text:", res_post.text)
    else:
        print("Login Failed:", res_login.text)


if __name__ == "__main__":
    main()
