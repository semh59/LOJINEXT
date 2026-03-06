import urllib.request
import urllib.error
import json


def test_endpoint(url):
    print(f"Testing {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as response:
            data = response.read()
            print("Status:", response.status)
            print("Response:", json.loads(data))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print("Status:", e.code)
        try:
            print("Error JSON:", json.loads(body))
        except:
            print("Error HTML/Text:", body)
    except Exception as e:
        print("Failed to connect:", e)


print("--- Testing API Endpoints ---")
# Using the trailers read endpoint, no auth required usually or we might get 401
test_endpoint("http://localhost:8000/api/v1/trailers/")
test_endpoint("http://127.0.0.1:8000/api/v1/trailers/")
