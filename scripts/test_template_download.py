
import httpx
import asyncio

async def test_template_download():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Login to get token
        login_res = await client.post(
            "http://localhost:8000/api/v1/auth/token",
            data={"username": "skara", "password": "!23efe25ali!"}
        )
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Download template
        res = await client.get(
            "http://localhost:8000/api/v1/vehicles/template",
            headers=headers
        )
        
        print(f"Status Code: {res.status_code}")
        print(f"Response Body: {res.text}")
        print(f"Content-Type: {res.headers.get('content-type')}")
        print(f"Content-Disposition: {res.headers.get('content-disposition')}")
        print(f"File Size: {len(res.content)} bytes")
        
        if res.status_code == 200 and len(res.content) > 0:
            print("SUCCESS: Template downloaded successfully.")
        else:
            print("FAILURE: Template download failed.")

if __name__ == "__main__":
    asyncio.run(test_template_download())
