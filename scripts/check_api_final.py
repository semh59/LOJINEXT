import asyncio
import httpx


async def check_api():
    url = "http://localhost:8000/api/v1/guzergahlar/?active_only=false"
    async with httpx.AsyncClient() as client:
        # We don't have an easy way to get a token here without knowing a password,
        # but let's see if we get a 200 or 401.
        try:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Count: {len(data)}")
                if data:
                    print(f"First item: {data[0]}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(check_api())
