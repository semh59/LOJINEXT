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

__all__ = [
    'AracRepository',
    'SoforRepository',
    'LokasyonRepository',
    'YakitRepository',
    'SeferRepository',
    'KullaniciRepository',
    'AnalizRepository',
]
