import httpx
import asyncio

async def diagnose_auth():
    print("🚀 Diagnosing skara auth for locations...")
    
    # 1. Get Token
    async with httpx.AsyncClient() as client:
        login_url = "http://127.0.0.1:8000/api/v1/auth/token"
        data = {
            "username": "skara",
            "password": "!23efe25ali!"
        }
        resp = await client.post(login_url, data=data)
        if resp.status_code != 200:
            print(f"❌ Login failed: {resp.status_code} {resp.text}")
            return
        
        token = resp.json()["access_token"]
        print(f"✅ Token obtained: {token[:20]}...")
        
        # 2. Call /auth/me
        me_url = "http://127.0.0.1:8000/api/v1/auth/me"
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(me_url, headers=headers)
        print(f"👤 /auth/me: {resp.status_code} {resp.text}")
        
        # 3. Call /locations/
        loc_url = "http://127.0.0.1:8000/api/v1/locations/"
        resp = await client.get(loc_url, headers=headers)
        print(f"📍 /locations/: {resp.status_code} {resp.text}")

        # 4. Call /locations (no slash)
        loc_no_slash_url = "http://127.0.0.1:8000/api/v1/locations"
        resp = await client.get(loc_no_slash_url, headers=headers, follow_redirects=True)
        print(f"📍 /locations (no slash, follow redirect): {resp.status_code} {resp.text}")

if __name__ == "__main__":
    asyncio.run(diagnose_auth())
