import asyncio
import httpx


async def debug_login():
    url = "http://localhost:8000/api/v1/auth/token"
    # Found in app/api/v1/endpoints/auth.py
    creds = {"username": "skara", "password": "!23efe25ali!"}

    async with httpx.AsyncClient() as client:
        try:
            print(f"POST {url} with {creds}")
            res = await client.post(url, data=creds)
            print(f"Status: {res.status_code}")
            print(f"Body: {res.text}")

            if res.status_code == 200:
                print("Token keys:", res.json().keys())
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_login())
