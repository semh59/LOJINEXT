import asyncio
import httpx
import sys
import os
import logging

sys.path.append(os.getcwd())
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000/api/v1"
USERNAME = "skara"
PASSWORD = "!23efe25ali!"


async def verify_rag():
    logger.info("Authenticating...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{BASE_URL}/auth/token", data={"username": USERNAME, "password": PASSWORD}
        )
        token = resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    query = {"message": "34 RAG 99 plakalı araç filoda var mı?"}

    logger.info(f"Asking AI (60s timeout): {query['message']}")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/ai/chat", json=query, headers=headers
            )
            if response.status_code == 200:
                logger.info(f"AI Response: {response.json().get('response')}")
                return True
            else:
                logger.error(f"AI Failed: {response.status_code} {response.text}")
                return False
    except Exception as e:
        logger.error(f"AI Exception: {e}")
        return False


if __name__ == "__main__":
    if asyncio.run(verify_rag()):
        print("RAG_SUCCESS")
    else:
        print("RAG_FAIL")
