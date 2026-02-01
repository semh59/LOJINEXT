
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def debug_create():
    # 1. Login
    print("1. Logging in...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/token", data={
            "username": "admin",
            "password": "!23efe25ali!"
        })
        if resp.status_code != 200:
            print("Login Failed:", resp.text)
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
    except Exception as e:
        print(f"Login Exception: {e}")
        return

    # 2. POST /vehicles/
    print("\n2. Creating Vehicle '27UN195' ...")
    payload = {
        "plaka": "27UN195",
        "marka": "MERCEDES-BENZ",
        "model": "ACTROS-1848",
        "yil": 2022,
        "tank_kapasitesi": 600,
        "hedef_tuketim": 32.0,
        "bos_agirlik_kg": 8000.0,
        "hava_direnc_katsayisi": 0.7,
        "on_kesit_alani_m2": 8.5,
        "notlar": "Debug insertion"
    }
    
    resp = requests.post(f"{BASE_URL}/vehicles/", json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    print("Response Body:", resp.text)

if __name__ == "__main__":
    debug_create()
