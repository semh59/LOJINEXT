import asyncio
from datetime import datetime, timezone
from app.core.services.dashboard_service import get_dashboard_service


async def check_service():
    service = get_dashboard_service()
    today_utc = datetime.now(timezone.utc).date()
    # Force bypass cache by calling the repo method directly if needed,
    # but first let's see what the service says.
    summary = await service.get_dashboard_summary(today_utc)
    print(f"SERVICE SUMMARY: {summary}")


if __name__ == "__main__":
    asyncio.run(check_service())
