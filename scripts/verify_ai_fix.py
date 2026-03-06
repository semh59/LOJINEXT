import asyncio
import httpx
import time
import json
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"


async def login():
    url = f"{BASE_URL}/auth/token"
    # Credentials from debug_login.py
    data = {"username": "skara", "password": "!23efe25ali!"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"Logging in to {url}...")
            resp = await client.post(url, data=data)
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                print("Login successful!")
                return token
            else:
                print(f"Login failed: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f"Login error: {repr(e)}")
            return None


async def check_status(token):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/ai/status", headers=headers)
            print(f"Status: {resp.json()}")
            return resp.json()
        except Exception as e:
            print(f"Status check failed: {repr(e)}")
            return None


async def trigger_chat(token):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("Triggering chat...")
            resp = await client.post(
                f"{BASE_URL}/ai/chat",
                json={"message": "Merhaba", "history": []},
                headers=headers,
            )
            print(f"Chat Response: {resp.json()}")
        except Exception as e:
            print(f"Chat trigger failed: {repr(e)}")


async def main():
    print("--- Starting AI Verify ---")

    token = await login()
    if not token:
        print("FATAL: Could not get auth token")
        return

    # 1. Check initial status
    await check_status(token)

    # 2. Trigger chat (should start loading)
    await trigger_chat(token)

    # 3. Monitor status for 10 seconds
    for _ in range(5):
        await asyncio.sleep(2)
        status = await check_status(token)
        if status and status.get("progress", {}).get("status") == "ready":
            print("Model READY!")
            break

    # 4. Trigger chat again if ready
    await trigger_chat(token)


if __name__ == "__main__":
    asyncio.run(main())
