import asyncio
import sys
import os

# Project Root
sys.path.append(os.getcwd())

from app.core.ml.ensemble_predictor import get_ensemble_service
from app.infrastructure.logging.logger import setup_logging


async def debug_train():
    setup_logging("debug")
    service = get_ensemble_service()
    print("Starting debug training for Vehicle 10...")
    result = await service.train_for_vehicle(10)
    print("Result:", result)


if __name__ == "__main__":
    asyncio.run(debug_train())
