import httpx
import asyncio
import sys


async def main():
    print("Inside main")
    try:
        async with httpx.AsyncClient() as client:
            print("Client created")
            try:
                resp = await client.get("http://localhost:8000/docs")
                print(f"Status: {resp.status_code}")
            except Exception as e:
                print(f"Request failed: {e}")
    except Exception as e:
        print(f"Client init failed: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception as e:
            print(f"Loop policy error: {e}")
    asyncio.run(main())
