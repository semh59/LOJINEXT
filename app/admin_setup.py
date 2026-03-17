"""
Legacy entrypoint for bootstrap admin setup.

Keeps the old script path working while delegating to the current async
admin bootstrap implementation.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scripts.create_admin import create_user


if __name__ == "__main__":
    asyncio.run(create_user())
