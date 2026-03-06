import httpx
import sys


def test_login():
    url = "http://127.0.0.1:8000/api/v1/auth/token"
    # Admin credentials from elite_audit_backend.py
    username = "skara"
    password = "!23efe25ali!"

    try:
        r = httpx.post(
            url,
            data={"username": username, "password": password},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_login()
