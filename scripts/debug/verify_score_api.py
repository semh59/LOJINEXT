
import asyncio
import httpx

async def verify_score_api():
    async with httpx.AsyncClient() as client:
        # Get token
        try:
            resp = await client.post("http://127.0.0.1:8000/api/v1/auth/token", data={
                "username": "skara",
                "password": "!23efe25ali!"
            })
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get a driver
            resp = await client.get("http://127.0.0.1:8000/api/v1/drivers/", headers=headers)
            drivers = resp.json()
            if not drivers:
                print("No drivers to test.")
                return
            
            driver_id = drivers[0]["id"]
            print(f"Testing driver {driver_id} scoring...")
            
            # Test updateScore (Correct range)
            resp = await client.post(f"http://127.0.0.1:8000/api/v1/drivers/{driver_id}/score?score=1.8", headers=headers)
            if resp.status_code == 200:
                print(f"PASS: Scoring 1.8 successful. New score: {resp.json()['manual_score']}")
            else:
                print(f"FAIL: Scoring 1.8 failed. Status: {resp.status_code}, Body: {resp.text}")

            # Test invalid range (3.0)
            resp = await client.post(f"http://127.0.0.1:8000/api/v1/drivers/{driver_id}/score?score=3.0", headers=headers)
            if resp.status_code == 400:
                print("PASS: Invalid score (3.0) correctly rejected with 400.")
            else:
                print(f"FAIL: Invalid score (3.0) not correctly rejected. Status: {resp.status_code}")

        except Exception as e:
            print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    asyncio.run(verify_score_api())
