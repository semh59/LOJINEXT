import urllib.request
import urllib.error
import json


def test_create_trailer(url, token):
    print(f"Testing POST {url} ...")

    data = {
        "plaka": "34 VRL 123",
        "marka": "Krone",
        "tipi": "Standart",
        "yil": 2024,
        "bos_agirlik_kg": 6000.0,
        "maks_yuk_kapasitesi_kg": 24000,
        "lastik_sayisi": 6,
    }
    encoded_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=encoded_data,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read()
            print("Status:", response.status)
            print("Response:", json.loads(res_data))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print("Status:", e.code)
        try:
            print("Error JSON:", json.loads(body))
        except:
            print("Error HTML/Text:", body)
    except Exception as e:
        print("Failed to connect:", e)


# The user is probably logging in through the UI right now, so we need a token to test it fully, but first let's see what the backend does.
print("--- Testing API Endpoint ---")
test_create_trailer("http://127.0.0.1:8000/api/v1/trailers/", "test_fake_token")
