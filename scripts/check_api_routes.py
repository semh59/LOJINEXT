import asyncio
import httpx


async def check_guzergahlar():
    url = "http://localhost:8000/api/v1/guzergahlar/"
    async with httpx.AsyncClient() as client:
        # Try without auth first to see if it even responds
        try:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_guzergahlar())
