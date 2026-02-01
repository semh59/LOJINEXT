"""
Interfaces Package
"""
from .repositories import (
    BaseRepository,
    IAracRepository,
    ILokasyonRepository,
    IPeriyotRepository,
    ISeferRepository,
    ISoforRepository,
    IYakitRepository,
)

__all__ = [
    "BaseRepository",
    "IAracRepository",
    "ISoforRepository",
    "IYakitRepository",
    "ISeferRepository",
    "ILokasyonRepository",
    "IPeriyotRepository",
]
