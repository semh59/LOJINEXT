"""
TIR Yakıt Takip - Repository Module
Domain-specific repository classes
"""

from app.database.repositories.analiz_repo import AnalizRepository
from app.database.repositories.arac_repo import AracRepository
from app.database.repositories.kullanici_repo import KullaniciRepository
from app.database.repositories.lokasyon_repo import LokasyonRepository
from app.database.repositories.sefer_repo import SeferRepository
from app.database.repositories.sofor_repo import SoforRepository
from app.database.repositories.yakit_repo import YakitRepository
from app.database.repositories.dorse_repo import DorseRepository, get_dorse_repo
from app.database.repositories.admin_config_repo import (
    AdminConfigRepository,
    get_admin_config_repo,
)

__all__ = [
    "AnalizRepository",
    "AracRepository",
    "KullaniciRepository",
    "LokasyonRepository",
    "SeferRepository",
    "SoforRepository",
    "YakitRepository",
    "DorseRepository",
    "get_dorse_repo",
    "AdminConfigRepository",
    "get_admin_config_repo",
]
