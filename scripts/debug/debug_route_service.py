import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Add root to python path
sys.path.append(os.getcwd())

from app.services.route_service import RouteService

async def main():
    print("Testing RouteService (Isolating DB)...")
    
    # Mock get_uow to avoid DB connection
    mock_uow = MagicMock()
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.__aexit__.return_value = None
    
    # Mock repos inside uow
    mock_uow.route_repo.get_by_coords = AsyncMock(return_value=None)
    mock_uow.route_repo.save_route = AsyncMock(return_value=None)
    
    # Check Env
    api_key_env = os.getenv("OPENROUTE_API_KEY")
    print(f"ENV KEY: {api_key_env[:5] if api_key_env else 'None'}")
    
    # Patch get_uow in route_service module
    with patch("app.services.route_service.get_uow", return_value=mock_uow):
        service = RouteService()
        if not service.api_key:
             print("SERVICE: API Key missing in service instance")
             # Try to set it specifically for test if env is missing but hardcoded for debug
             # service.api_key = "YOUR_KEY" 
        
        start = (28.9784, 41.0082) 
        end = (32.8597, 39.9334)
        
        print(f"Fetching route from {start} to {end}...")
        try:
            result = await service.get_route_details(start, end, use_cache=False)
            if "error" in result:
                print(f"FAILED: {result['error']}")
            else:
                 print("SUCCESS")
                 print(result)
        except Exception as e:
            print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(main())
