import urllib.request
import json
import urllib.error

url_base = "http://localhost:8000/api/v1"
auth_data = "username=skara&password=!23efe25ali!".encode("utf-8")

try:
    # 1. Login
    req = urllib.request.Request(f"{url_base}/auth/token", data=auth_data, method="POST")
    # req.add_header("Content-Type", "application/x-www-form-urlencoded") # Default
    
    with urllib.request.urlopen(req) as f:
        res = json.load(f)
        token = res["access_token"]
        print("Login Successful.")

    # 2. Create Trip
    trip_data = {
      "tarih": "2026-01-31",
      "saat": "12:00",
      "arac_id": 1, 
      "sofor_id": 1,
      "cikis_yeri": "Test Cikis",
      "varis_yeri": "Test Varis",
      "mesafe_km": 100,
      "net_kg": 0,
      "bos_sefer": False,
      "ascent_m": 0,
      "descent_m": 0,
      "durum": "Tamam"
    }

    print("Sending Trip Data:", json.dumps(trip_data))
    
    jsondata = json.dumps(trip_data).encode("utf-8")
    req = urllib.request.Request(f"{url_base}/trips/", data=jsondata, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req) as f:
        print("Status:", f.status)
        print("Response:", f.read().decode())

except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Error Body:", e.read().decode())
    
except Exception as e:
    print(f"Exception: {e}")
