r"""
LOJINEXT Elite Data Synthesis — 20K Realistic Trips
====================================================
Generates a complete, realistic dataset for ML training:
- 25 vehicles (8 TIR archetypes)
- 40 drivers (realistic performance spread)
- 30+ Turkish route archetypes with real coordinates
- 20,000 trips with physics-based fuel consumption
- Linked fuel records (YakitAlimi)

Usage:
    cd d:\PROJECT\LOJINEXT
    python scripts/synthesize_20k_realistic.py
"""

import asyncio
import random
import sys
import os
import math
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple
from decimal import Decimal

# Project Root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import delete, text
from app.database.connection import AsyncSessionLocal
from app.database.models import (
    Arac,
    Sofor,
    Sefer,
    YakitAlimi,
    Lokasyon,
    YakitPeriyodu,
    YakitFormul,
    Anomaly,
    Alert,
    RoutePath,
    ModelVersion,
)
from app.core.ml.physics_fuel_predictor import (
    PhysicsBasedFuelPredictor,
    RouteConditions,
    VehicleSpecs,
)
from app.infrastructure.logging.logger import setup_logging

logger = setup_logging("synthesis_20k")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

VEHICLE_COUNT = 25
DRIVER_COUNT = 40
TRIPS_PER_VEHICLE = 800  # 25 * 800 = 20,000
START_DATE = datetime(2025, 6, 1)
END_DATE = datetime(2026, 2, 15)
BATCH_SIZE = 500  # Flush to DB every N trips

# ══════════════════════════════════════════════════════════════════════════════
# VEHICLE ARCHETYPES — Real TIR Fleet Models
# ══════════════════════════════════════════════════════════════════════════════

VEHICLE_ARCHETYPES = [
    {
        "marka": "Mercedes-Benz",
        "model": "Actros 1845",
        "yil": 2024,
        "tank": 650,
        "bos_kg": 14200,
        "cd": 0.62,
        "area": 8.1,
        "eff": 0.41,
    },
    {
        "marka": "Mercedes-Benz",
        "model": "Actros 1848",
        "yil": 2025,
        "tank": 700,
        "bos_kg": 14500,
        "cd": 0.60,
        "area": 8.0,
        "eff": 0.42,
    },
    {
        "marka": "Scania",
        "model": "R450",
        "yil": 2023,
        "tank": 700,
        "bos_kg": 14800,
        "cd": 0.63,
        "area": 8.3,
        "eff": 0.40,
    },
    {
        "marka": "Scania",
        "model": "S500",
        "yil": 2024,
        "tank": 750,
        "bos_kg": 15000,
        "cd": 0.58,
        "area": 8.0,
        "eff": 0.42,
    },
    {
        "marka": "Volvo",
        "model": "FH13 500",
        "yil": 2025,
        "tank": 750,
        "bos_kg": 14600,
        "cd": 0.60,
        "area": 8.2,
        "eff": 0.41,
    },
    {
        "marka": "MAN",
        "model": "TGX 18.440",
        "yil": 2022,
        "tank": 600,
        "bos_kg": 14300,
        "cd": 0.65,
        "area": 8.4,
        "eff": 0.39,
    },
    {
        "marka": "DAF",
        "model": "XF 480",
        "yil": 2023,
        "tank": 650,
        "bos_kg": 14400,
        "cd": 0.64,
        "area": 8.3,
        "eff": 0.40,
    },
    {
        "marka": "Ford",
        "model": "F-MAX 500",
        "yil": 2024,
        "tank": 650,
        "bos_kg": 14100,
        "cd": 0.66,
        "area": 8.5,
        "eff": 0.39,
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# ROUTE ARCHETYPES — 30 Real Turkish Routes
# ══════════════════════════════════════════════════════════════════════════════
# Each route has real coordinates, calibrated road analysis, and difficulty.
# road_analysis format matches RouteAnalyzer output.
# otoban_pct is used to split otoban_mesafe_km vs sehir_ici_mesafe_km.

ROUTE_ARCHETYPES: List[Dict[str, Any]] = [
    # 1. Istanbul → Ankara (O-4 Otoyolu)
    {
        "cikis": "İstanbul",
        "varis": "Ankara",
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 39.9334,
        "varis_lon": 32.8597,
        "mesafe": 453,
        "ascent": 800,
        "descent": 750,
        "zorluk": "Normal",
        "sensitivity": 0.9,
        "otoban_pct": 0.85,
        "road_analysis": {
            "motorway": {"flat": 280, "up": 50, "down": 55},
            "trunk": {"flat": 20, "up": 5, "down": 3},
            "primary": {"flat": 25, "up": 8, "down": 7},
            "highway": {"flat": 325, "up": 63, "down": 65},
            "other": {"flat": 0, "up": 0, "down": 0},
        },
    },
    # 2. Istanbul → Erzurum (O-4 + E-80, dağlık)
    {
        "cikis": "İstanbul",
        "varis": "Erzurum",
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 39.9043,
        "varis_lon": 41.2679,
        "mesafe": 1230,
        "ascent": 2200,
        "descent": 1500,
        "zorluk": "Zor",
        "sensitivity": 1.2,
        "otoban_pct": 0.55,
        "road_analysis": {
            "motorway": {"flat": 350, "up": 80, "down": 70},
            "trunk": {"flat": 200, "up": 60, "down": 50},
            "primary": {"flat": 150, "up": 120, "down": 100},
            "highway": {"flat": 700, "up": 260, "down": 220},
            "other": {"flat": 20, "up": 15, "down": 15},
        },
    },
    # 3. Bursa → İzmir (O-2 Otoyolu)
    {
        "cikis": "Bursa",
        "varis": "İzmir",
        "cikis_lat": 40.1885,
        "cikis_lon": 29.0610,
        "varis_lat": 38.4192,
        "varis_lon": 27.1287,
        "mesafe": 345,
        "ascent": 300,
        "descent": 300,
        "zorluk": "Kolay",
        "sensitivity": 0.7,
        "otoban_pct": 0.90,
        "road_analysis": {
            "motorway": {"flat": 260, "up": 25, "down": 25},
            "trunk": {"flat": 20, "up": 5, "down": 5},
            "primary": {"flat": 5, "up": 0, "down": 0},
            "highway": {"flat": 285, "up": 30, "down": 30},
            "other": {"flat": 0, "up": 0, "down": 0},
        },
    },
    # 4. Ankara → Konya (O-21 Otoyolu)
    {
        "cikis": "Ankara",
        "varis": "Konya",
        "cikis_lat": 39.9334,
        "cikis_lon": 32.8597,
        "varis_lat": 37.8746,
        "varis_lon": 32.4932,
        "mesafe": 260,
        "ascent": 200,
        "descent": 150,
        "zorluk": "Kolay",
        "sensitivity": 0.8,
        "otoban_pct": 0.95,
        "road_analysis": {
            "motorway": {"flat": 230, "up": 10, "down": 8},
            "trunk": {"flat": 8, "up": 2, "down": 2},
            "primary": {"flat": 0, "up": 0, "down": 0},
            "highway": {"flat": 238, "up": 12, "down": 10},
            "other": {"flat": 0, "up": 0, "down": 0},
        },
    },
    # 5. Antalya → Mersin (D-400, dağlık kıyı)
    {
        "cikis": "Antalya",
        "varis": "Mersin",
        "cikis_lat": 36.8969,
        "cikis_lon": 30.7133,
        "varis_lat": 36.8121,
        "varis_lon": 34.6415,
        "mesafe": 480,
        "ascent": 1200,
        "descent": 1200,
        "zorluk": "Zor",
        "sensitivity": 1.1,
        "otoban_pct": 0.20,
        "road_analysis": {
            "motorway": {"flat": 30, "up": 10, "down": 10},
            "trunk": {"flat": 60, "up": 30, "down": 30},
            "primary": {"flat": 100, "up": 80, "down": 80},
            "highway": {"flat": 190, "up": 120, "down": 120},
            "other": {"flat": 20, "up": 15, "down": 15},
        },
    },
    # 6. Lüleburgaz → İstanbul (O-3 TEM)
    {
        "cikis": "Lüleburgaz",
        "varis": "İstanbul",
        "cikis_lat": 41.4048,
        "cikis_lon": 27.3575,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 160,
        "ascent": 150,
        "descent": 150,
        "zorluk": "Kolay",
        "sensitivity": 0.8,
        "otoban_pct": 0.92,
        "road_analysis": {
            "motorway": {"flat": 130, "up": 8, "down": 8},
            "trunk": {"flat": 8, "up": 2, "down": 2},
            "primary": {"flat": 2, "up": 0, "down": 0},
            "highway": {"flat": 140, "up": 10, "down": 10},
            "other": {"flat": 0, "up": 0, "down": 0},
        },
    },
    # 7. Istanbul → Trabzon (kıyı + dağ)
    {
        "cikis": "İstanbul",
        "varis": "Trabzon",
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 41.0027,
        "varis_lon": 39.7168,
        "mesafe": 1070,
        "ascent": 1800,
        "descent": 1600,
        "zorluk": "Zor",
        "sensitivity": 1.15,
        "otoban_pct": 0.50,
        "road_analysis": {
            "motorway": {"flat": 280, "up": 60, "down": 55},
            "trunk": {"flat": 100, "up": 40, "down": 35},
            "primary": {"flat": 150, "up": 100, "down": 90},
            "highway": {"flat": 530, "up": 200, "down": 180},
            "other": {"flat": 60, "up": 50, "down": 50},
        },
    },
    # 8. Ankara → İzmir (O-5/O-31)
    {
        "cikis": "Ankara",
        "varis": "İzmir",
        "cikis_lat": 39.9334,
        "cikis_lon": 32.8597,
        "varis_lat": 38.4192,
        "varis_lon": 27.1287,
        "mesafe": 586,
        "ascent": 900,
        "descent": 850,
        "zorluk": "Normal",
        "sensitivity": 0.95,
        "otoban_pct": 0.70,
        "road_analysis": {
            "motorway": {"flat": 280, "up": 50, "down": 45},
            "trunk": {"flat": 50, "up": 15, "down": 12},
            "primary": {"flat": 60, "up": 30, "down": 25},
            "highway": {"flat": 390, "up": 95, "down": 82},
            "other": {"flat": 8, "up": 6, "down": 5},
        },
    },
    # 9. Istanbul → Mersin (O-4 + O-21 + Toros)
    {
        "cikis": "İstanbul",
        "varis": "Mersin",
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 36.8121,
        "varis_lon": 34.6415,
        "mesafe": 940,
        "ascent": 1100,
        "descent": 1050,
        "zorluk": "Normal",
        "sensitivity": 1.0,
        "otoban_pct": 0.80,
        "road_analysis": {
            "motorway": {"flat": 530, "up": 80, "down": 75},
            "trunk": {"flat": 60, "up": 20, "down": 18},
            "primary": {"flat": 60, "up": 40, "down": 35},
            "highway": {"flat": 650, "up": 140, "down": 128},
            "other": {"flat": 10, "up": 6, "down": 6},
        },
    },
    # 10. Istanbul → Antalya (O-4 + Burdur)
    {
        "cikis": "İstanbul",
        "varis": "Antalya",
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 36.8969,
        "varis_lon": 30.7133,
        "mesafe": 720,
        "ascent": 950,
        "descent": 900,
        "zorluk": "Normal",
        "sensitivity": 0.95,
        "otoban_pct": 0.75,
        "road_analysis": {
            "motorway": {"flat": 380, "up": 60, "down": 55},
            "trunk": {"flat": 50, "up": 20, "down": 15},
            "primary": {"flat": 50, "up": 35, "down": 30},
            "highway": {"flat": 480, "up": 115, "down": 100},
            "other": {"flat": 10, "up": 8, "down": 7},
        },
    },
    # 11. Ankara → Adana (Toros geçidi)
    {
        "cikis": "Ankara",
        "varis": "Adana",
        "cikis_lat": 39.9334,
        "cikis_lon": 32.8597,
        "varis_lat": 36.9914,
        "varis_lon": 35.3308,
        "mesafe": 490,
        "ascent": 1400,
        "descent": 1350,
        "zorluk": "Zor",
        "sensitivity": 1.15,
        "otoban_pct": 0.55,
        "road_analysis": {
            "motorway": {"flat": 120, "up": 40, "down": 35},
            "trunk": {"flat": 60, "up": 30, "down": 25},
            "primary": {"flat": 60, "up": 50, "down": 45},
            "highway": {"flat": 240, "up": 120, "down": 105},
            "other": {"flat": 10, "up": 8, "down": 7},
        },
    },
    # 12. İzmir → Antalya (D-400 kıyı)
    {
        "cikis": "İzmir",
        "varis": "Antalya",
        "cikis_lat": 38.4192,
        "cikis_lon": 27.1287,
        "varis_lat": 36.8969,
        "varis_lon": 30.7133,
        "mesafe": 460,
        "ascent": 800,
        "descent": 750,
        "zorluk": "Normal",
        "sensitivity": 0.95,
        "otoban_pct": 0.40,
        "road_analysis": {
            "motorway": {"flat": 80, "up": 20, "down": 15},
            "trunk": {"flat": 50, "up": 15, "down": 12},
            "primary": {"flat": 100, "up": 60, "down": 55},
            "highway": {"flat": 230, "up": 95, "down": 82},
            "other": {"flat": 20, "up": 18, "down": 15},
        },
    },
    # 13. Eskişehir → İstanbul (O-4)
    {
        "cikis": "Eskişehir",
        "varis": "İstanbul",
        "cikis_lat": 39.7767,
        "cikis_lon": 30.5206,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 330,
        "ascent": 400,
        "descent": 350,
        "zorluk": "Normal",
        "sensitivity": 0.85,
        "otoban_pct": 0.85,
        "road_analysis": {
            "motorway": {"flat": 230, "up": 25, "down": 22},
            "trunk": {"flat": 15, "up": 5, "down": 3},
            "primary": {"flat": 15, "up": 8, "down": 7},
            "highway": {"flat": 260, "up": 38, "down": 32},
            "other": {"flat": 0, "up": 0, "down": 0},
        },
    },
    # 14. Gaziantep → İstanbul (O-52 + O-4)
    {
        "cikis": "Gaziantep",
        "varis": "İstanbul",
        "cikis_lat": 37.0662,
        "cikis_lon": 37.3833,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 1130,
        "ascent": 1200,
        "descent": 1150,
        "zorluk": "Normal",
        "sensitivity": 1.0,
        "otoban_pct": 0.72,
        "road_analysis": {
            "motorway": {"flat": 550, "up": 80, "down": 75},
            "trunk": {"flat": 80, "up": 25, "down": 20},
            "primary": {"flat": 100, "up": 60, "down": 55},
            "highway": {"flat": 730, "up": 165, "down": 150},
            "other": {"flat": 30, "up": 30, "down": 25},
        },
    },
    # 15. Konya → Adana (Toros geçidi)
    {
        "cikis": "Konya",
        "varis": "Adana",
        "cikis_lat": 37.8746,
        "cikis_lon": 32.4932,
        "varis_lat": 36.9914,
        "varis_lon": 35.3308,
        "mesafe": 340,
        "ascent": 1300,
        "descent": 1250,
        "zorluk": "Zor",
        "sensitivity": 1.2,
        "otoban_pct": 0.45,
        "road_analysis": {
            "motorway": {"flat": 60, "up": 20, "down": 18},
            "trunk": {"flat": 40, "up": 20, "down": 15},
            "primary": {"flat": 50, "up": 45, "down": 40},
            "highway": {"flat": 150, "up": 85, "down": 73},
            "other": {"flat": 12, "up": 10, "down": 10},
        },
    },
    # 16. Samsun → Ankara (D-795)
    {
        "cikis": "Samsun",
        "varis": "Ankara",
        "cikis_lat": 41.2867,
        "cikis_lon": 36.33,
        "varis_lat": 39.9334,
        "varis_lon": 32.8597,
        "mesafe": 420,
        "ascent": 700,
        "descent": 650,
        "zorluk": "Normal",
        "sensitivity": 0.95,
        "otoban_pct": 0.40,
        "road_analysis": {
            "motorway": {"flat": 50, "up": 15, "down": 12},
            "trunk": {"flat": 60, "up": 20, "down": 18},
            "primary": {"flat": 100, "up": 50, "down": 45},
            "highway": {"flat": 210, "up": 85, "down": 75},
            "other": {"flat": 20, "up": 15, "down": 15},
        },
    },
    # 17. Istanbul → Diyarbakır (O-4 + E-80)
    {
        "cikis": "İstanbul",
        "varis": "Diyarbakır",
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 37.9158,
        "varis_lon": 40.2189,
        "mesafe": 1370,
        "ascent": 2000,
        "descent": 1800,
        "zorluk": "Çok Zor",
        "sensitivity": 1.25,
        "otoban_pct": 0.55,
        "road_analysis": {
            "motorway": {"flat": 400, "up": 90, "down": 80},
            "trunk": {"flat": 150, "up": 50, "down": 45},
            "primary": {"flat": 180, "up": 120, "down": 100},
            "highway": {"flat": 730, "up": 260, "down": 225},
            "other": {"flat": 50, "up": 55, "down": 50},
        },
    },
    # 18. Tekirdağ → İstanbul (O-6 TEM)
    {
        "cikis": "Tekirdağ",
        "varis": "İstanbul",
        "cikis_lat": 40.9833,
        "cikis_lon": 27.5167,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 135,
        "ascent": 100,
        "descent": 100,
        "zorluk": "Kolay",
        "sensitivity": 0.7,
        "otoban_pct": 0.93,
        "road_analysis": {
            "motorway": {"flat": 110, "up": 6, "down": 6},
            "trunk": {"flat": 8, "up": 2, "down": 1},
            "primary": {"flat": 2, "up": 0, "down": 0},
            "highway": {"flat": 120, "up": 8, "down": 7},
            "other": {"flat": 0, "up": 0, "down": 0},
        },
    },
    # 19. İstanbul → Edirne (O-3 TEM)
    {
        "cikis": "İstanbul",
        "varis": "Edirne",
        "cikis_lat": 41.0082,
        "cikis_lon": 28.9784,
        "varis_lat": 41.6818,
        "varis_lon": 26.5623,
        "mesafe": 235,
        "ascent": 150,
        "descent": 140,
        "zorluk": "Kolay",
        "sensitivity": 0.75,
        "otoban_pct": 0.95,
        "road_analysis": {
            "motorway": {"flat": 200, "up": 10, "down": 9},
            "trunk": {"flat": 10, "up": 2, "down": 2},
            "primary": {"flat": 2, "up": 0, "down": 0},
            "highway": {"flat": 212, "up": 12, "down": 11},
            "other": {"flat": 0, "up": 0, "down": 0},
        },
    },
    # 20. Kayseri → İstanbul (O-4 + O-21)
    {
        "cikis": "Kayseri",
        "varis": "İstanbul",
        "cikis_lat": 38.7312,
        "cikis_lon": 35.4787,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 770,
        "ascent": 800,
        "descent": 750,
        "zorluk": "Normal",
        "sensitivity": 0.9,
        "otoban_pct": 0.70,
        "road_analysis": {
            "motorway": {"flat": 360, "up": 60, "down": 55},
            "trunk": {"flat": 60, "up": 20, "down": 15},
            "primary": {"flat": 80, "up": 50, "down": 40},
            "highway": {"flat": 500, "up": 130, "down": 110},
            "other": {"flat": 12, "up": 10, "down": 8},
        },
    },
    # 21. Bursa → Ankara (O-4/Bolu)
    {
        "cikis": "Bursa",
        "varis": "Ankara",
        "cikis_lat": 40.1885,
        "cikis_lon": 29.0610,
        "varis_lat": 39.9334,
        "varis_lon": 32.8597,
        "mesafe": 380,
        "ascent": 500,
        "descent": 450,
        "zorluk": "Normal",
        "sensitivity": 0.85,
        "otoban_pct": 0.78,
        "road_analysis": {
            "motorway": {"flat": 220, "up": 35, "down": 30},
            "trunk": {"flat": 30, "up": 10, "down": 8},
            "primary": {"flat": 20, "up": 12, "down": 10},
            "highway": {"flat": 270, "up": 57, "down": 48},
            "other": {"flat": 2, "up": 2, "down": 1},
        },
    },
    # 22. Denizli → İzmir (O-31)
    {
        "cikis": "Denizli",
        "varis": "İzmir",
        "cikis_lat": 37.7765,
        "cikis_lon": 29.0864,
        "varis_lat": 38.4192,
        "varis_lon": 27.1287,
        "mesafe": 250,
        "ascent": 600,
        "descent": 550,
        "zorluk": "Normal",
        "sensitivity": 0.9,
        "otoban_pct": 0.50,
        "road_analysis": {
            "motorway": {"flat": 60, "up": 15, "down": 12},
            "trunk": {"flat": 30, "up": 10, "down": 8},
            "primary": {"flat": 40, "up": 25, "down": 22},
            "highway": {"flat": 130, "up": 50, "down": 42},
            "other": {"flat": 10, "up": 10, "down": 8},
        },
    },
    # 23. Trabzon → Erzurum (dağlık)
    {
        "cikis": "Trabzon",
        "varis": "Erzurum",
        "cikis_lat": 41.0027,
        "cikis_lon": 39.7168,
        "varis_lat": 39.9043,
        "varis_lon": 41.2679,
        "mesafe": 325,
        "ascent": 1500,
        "descent": 1200,
        "zorluk": "Çok Zor",
        "sensitivity": 1.3,
        "otoban_pct": 0.10,
        "road_analysis": {
            "motorway": {"flat": 0, "up": 0, "down": 0},
            "trunk": {"flat": 30, "up": 20, "down": 15},
            "primary": {"flat": 50, "up": 70, "down": 55},
            "highway": {"flat": 80, "up": 90, "down": 70},
            "other": {"flat": 30, "up": 30, "down": 25},
        },
    },
    # 24. Bolu → İstanbul (O-4 Bolu tüneli)
    {
        "cikis": "Bolu",
        "varis": "İstanbul",
        "cikis_lat": 40.7317,
        "cikis_lon": 31.6061,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 265,
        "ascent": 500,
        "descent": 450,
        "zorluk": "Normal",
        "sensitivity": 0.85,
        "otoban_pct": 0.90,
        "road_analysis": {
            "motorway": {"flat": 190, "up": 25, "down": 20},
            "trunk": {"flat": 10, "up": 5, "down": 3},
            "primary": {"flat": 5, "up": 3, "down": 2},
            "highway": {"flat": 205, "up": 33, "down": 25},
            "other": {"flat": 1, "up": 1, "down": 0},
        },
    },
    # 25. Ankara → Sivas (dağ yolu)
    {
        "cikis": "Ankara",
        "varis": "Sivas",
        "cikis_lat": 39.9334,
        "cikis_lon": 32.8597,
        "varis_lat": 39.7477,
        "varis_lon": 37.0179,
        "mesafe": 450,
        "ascent": 900,
        "descent": 800,
        "zorluk": "Zor",
        "sensitivity": 1.1,
        "otoban_pct": 0.30,
        "road_analysis": {
            "motorway": {"flat": 40, "up": 10, "down": 8},
            "trunk": {"flat": 40, "up": 15, "down": 12},
            "primary": {"flat": 100, "up": 70, "down": 60},
            "highway": {"flat": 180, "up": 95, "down": 80},
            "other": {"flat": 35, "up": 35, "down": 25},
        },
    },
    # 26. İzmit → Ankara (O-4)
    {
        "cikis": "İzmit",
        "varis": "Ankara",
        "cikis_lat": 40.7669,
        "cikis_lon": 29.9169,
        "varis_lat": 39.9334,
        "varis_lon": 32.8597,
        "mesafe": 340,
        "ascent": 600,
        "descent": 550,
        "zorluk": "Normal",
        "sensitivity": 0.85,
        "otoban_pct": 0.90,
        "road_analysis": {
            "motorway": {"flat": 240, "up": 35, "down": 30},
            "trunk": {"flat": 12, "up": 5, "down": 3},
            "primary": {"flat": 8, "up": 3, "down": 2},
            "highway": {"flat": 260, "up": 43, "down": 35},
            "other": {"flat": 1, "up": 1, "down": 0},
        },
    },
    # 27. Adana → Gaziantep (O-52)
    {
        "cikis": "Adana",
        "varis": "Gaziantep",
        "cikis_lat": 36.9914,
        "cikis_lon": 35.3308,
        "varis_lat": 37.0662,
        "varis_lon": 37.3833,
        "mesafe": 220,
        "ascent": 400,
        "descent": 350,
        "zorluk": "Normal",
        "sensitivity": 0.9,
        "otoban_pct": 0.70,
        "road_analysis": {
            "motorway": {"flat": 100, "up": 20, "down": 15},
            "trunk": {"flat": 20, "up": 8, "down": 5},
            "primary": {"flat": 20, "up": 12, "down": 10},
            "highway": {"flat": 140, "up": 40, "down": 30},
            "other": {"flat": 4, "up": 3, "down": 3},
        },
    },
    # 28. Aksaray → Ankara (O-21)
    {
        "cikis": "Aksaray",
        "varis": "Ankara",
        "cikis_lat": 38.3687,
        "cikis_lon": 34.0370,
        "varis_lat": 39.9334,
        "varis_lon": 32.8597,
        "mesafe": 230,
        "ascent": 250,
        "descent": 200,
        "zorluk": "Kolay",
        "sensitivity": 0.75,
        "otoban_pct": 0.82,
        "road_analysis": {
            "motorway": {"flat": 160, "up": 12, "down": 10},
            "trunk": {"flat": 15, "up": 5, "down": 3},
            "primary": {"flat": 10, "up": 5, "down": 5},
            "highway": {"flat": 185, "up": 22, "down": 18},
            "other": {"flat": 2, "up": 2, "down": 1},
        },
    },
    # 29. Afyon → İstanbul (O-7 Afyon-İstanbul)
    {
        "cikis": "Afyonkarahisar",
        "varis": "İstanbul",
        "cikis_lat": 38.7507,
        "cikis_lon": 30.5567,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 450,
        "ascent": 700,
        "descent": 650,
        "zorluk": "Normal",
        "sensitivity": 0.9,
        "otoban_pct": 0.65,
        "road_analysis": {
            "motorway": {"flat": 180, "up": 35, "down": 30},
            "trunk": {"flat": 40, "up": 15, "down": 12},
            "primary": {"flat": 50, "up": 30, "down": 25},
            "highway": {"flat": 270, "up": 80, "down": 67},
            "other": {"flat": 12, "up": 12, "down": 9},
        },
    },
    # 30. Çorum → İstanbul (D-785 + O-4)
    {
        "cikis": "Çorum",
        "varis": "İstanbul",
        "cikis_lat": 40.5506,
        "cikis_lon": 34.9556,
        "varis_lat": 41.0082,
        "varis_lon": 28.9784,
        "mesafe": 560,
        "ascent": 600,
        "descent": 550,
        "zorluk": "Normal",
        "sensitivity": 0.9,
        "otoban_pct": 0.50,
        "road_analysis": {
            "motorway": {"flat": 150, "up": 25, "down": 20},
            "trunk": {"flat": 40, "up": 10, "down": 8},
            "primary": {"flat": 100, "up": 50, "down": 45},
            "highway": {"flat": 290, "up": 85, "down": 73},
            "other": {"flat": 40, "up": 40, "down": 32},
        },
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# DRIVER NAMES — Realistic Turkish Names
# ══════════════════════════════════════════════════════════════════════════════

DRIVER_NAMES = [
    "Mehmet Yılmaz",
    "Ahmet Kaya",
    "Ali Demir",
    "Mustafa Şahin",
    "Hasan Çelik",
    "Hüseyin Yıldız",
    "İbrahim Aydın",
    "Murat Öztürk",
    "Osman Arslan",
    "Fatih Doğan",
    "Emre Kılıç",
    "Serkan Koç",
    "Burak Aksoy",
    "Cengiz Polat",
    "Deniz Erdoğan",
    "Erhan Çetin",
    "Ferhat Acar",
    "Gökhan Taş",
    "Halil Güneş",
    "İsmail Kurt",
    "Kadir Yalçın",
    "Levent Karaca",
    "Metin Şen",
    "Necati Özkan",
    "Orhan Aktaş",
    "Ramazan Ateş",
    "Selim Kaplan",
    "Tuncay Bal",
    "Uğur Duman",
    "Volkan Aslan",
    "Yakup Korkmaz",
    "Zafer Tunç",
    "Bayram Uçar",
    "Celal Avcı",
    "Davut Güler",
    "Ercan Bulut",
    "Faruk Sarı",
    "Gürsel Çakır",
    "Hamza Yüksel",
    "İlker Bayrak",
]

# Fuel station names
FUEL_STATIONS = [
    "Shell Otoyol",
    "BP Petrol",
    "Opet Terminal",
    "Total Energies",
    "Petrol Ofisi",
    "Lukoil TIR Park",
    "TP Petrol",
    "Alpet Station",
    "Go Motorin",
    "Kadoil Depo",
    "Milangaz Station",
    "ExxonMobil TR",
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


def get_seasonal_factor(trip_date: date) -> float:
    """
    Seasonal adjustment factor for fuel consumption.
    Winter = higher consumption, Summer = lower.
    """
    month = trip_date.month
    if month in (12, 1, 2):  # Winter
        return random.uniform(1.03, 1.08)
    elif month in (6, 7, 8):  # Summer
        return random.uniform(0.96, 1.00)
    elif month in (3, 4, 5):  # Spring
        return random.uniform(0.98, 1.02)
    else:  # Autumn
        return random.uniform(1.00, 1.04)


def get_vehicle_age_factor(yil: int) -> float:
    """Newer vehicles are slightly more fuel-efficient."""
    age = 2026 - yil
    if age <= 1:
        return 0.97  # New vehicle
    elif age <= 3:
        return 1.00
    elif age <= 5:
        return 1.02
    else:
        return 1.05  # Older vehicle


def calculate_road_metrics(arch: Dict, mesafe: float) -> Tuple[float, float, float]:
    """
    Calculate otoban_mesafe_km, sehir_ici_mesafe_km, flat_distance_km from archetype.
    """
    otoban_pct = arch["otoban_pct"]
    otoban_km = mesafe * otoban_pct
    sehir_ici_km = mesafe * (1 - otoban_pct)

    # flat_distance is sum of all flat portions
    ra = arch["road_analysis"]
    archetype_total = sum(
        sum(v.values())
        for k, v in ra.items()
        if k not in ("highway", "other") and isinstance(v, dict)
    )
    if archetype_total > 0:
        flat_total = sum(
            v.get("flat", 0)
            for k, v in ra.items()
            if k not in ("highway", "other") and isinstance(v, dict)
        )
        flat_pct = flat_total / archetype_total
    else:
        flat_pct = 0.7  # default
    flat_km = mesafe * flat_pct

    return round(otoban_km, 2), round(sehir_ici_km, 2), round(flat_km, 2)


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════


async def clear_all_data():
    """Delete all existing data and reset sequences."""
    logger.info("╔════════════════════════════════════════╗")
    logger.info("║  CLEARING ALL DATA                     ║")
    logger.info("╚════════════════════════════════════════╝")

    async with AsyncSessionLocal() as session:
        # Dependency order
        await session.execute(delete(YakitFormul))
        await session.execute(delete(Anomaly))
        await session.execute(delete(Alert))
        await session.execute(delete(RoutePath))
        await session.execute(delete(ModelVersion))
        await session.execute(delete(YakitPeriyodu))
        await session.execute(delete(YakitAlimi))
        await session.execute(delete(Sefer))
        await session.execute(delete(Lokasyon))
        await session.execute(delete(Arac))
        await session.execute(delete(Sofor))
        await session.commit()

        # Reset sequences
        tables = [
            "yakit_formul",
            "anomalies",
            "alerts",
            "route_paths",
            "model_versions",
            "yakit_periyotlari",
            "yakit_alimlari",
            "seferler",
            "lokasyonlar",
            "araclar",
            "soforler",
        ]
        for t in tables:
            try:
                await session.execute(text(f"ALTER SEQUENCE {t}_id_seq RESTART WITH 1"))
            except Exception:
                pass  # Table might not have a sequence
        await session.commit()

    logger.info("✅ All data cleared.")


async def create_master_data() -> Tuple[List, List, List]:
    """Create vehicles, drivers, and route lokasyonlar."""
    logger.info("╔════════════════════════════════════════╗")
    logger.info("║  CREATING MASTER DATA                  ║")
    logger.info("╚════════════════════════════════════════╝")

    async with AsyncSessionLocal() as session:
        # ── 1. Lokasyonlar (Routes) ──
        master_routes = []
        for arch in ROUTE_ARCHETYPES:
            lok = Lokasyon(
                cikis_yeri=arch["cikis"],
                varis_yeri=arch["varis"],
                mesafe_km=float(arch["mesafe"]),
                zorluk=arch["zorluk"],
                ascent_m=float(arch["ascent"]),
                descent_m=float(arch["descent"]),
                cikis_lat=arch["cikis_lat"],
                cikis_lon=arch["cikis_lon"],
                varis_lat=arch["varis_lat"],
                varis_lon=arch["varis_lon"],
                otoban_mesafe_km=round(arch["mesafe"] * arch["otoban_pct"], 2),
                sehir_ici_mesafe_km=round(arch["mesafe"] * (1 - arch["otoban_pct"]), 2),
                flat_distance_km=round(arch["mesafe"] * 0.65, 2),
                route_analysis=arch["road_analysis"],
                source="synthesis_v3",
                aktif=True,
            )
            session.add(lok)
            master_routes.append({"arch": arch, "entity": lok})

        # ── 2. Drivers (Şoförler) ──
        drivers = []
        for i in range(DRIVER_COUNT):
            # Realistic performance distribution: most are average, few are outliers
            score = round(np.clip(np.random.normal(1.0, 0.06), 0.85, 1.20), 3)
            hiz_skor = round(np.clip(np.random.normal(1.0, 0.05), 0.90, 1.15), 3)
            agresif = round(np.clip(np.random.normal(1.0, 0.04), 0.92, 1.12), 3)
            # Phase 5A: Elite Driver Factors
            ramp_skoru = round(np.clip(np.random.normal(1.0, 0.08), 0.80, 1.25), 3)
            istikrar = round(np.clip(np.random.normal(1.0, 0.03), 0.94, 1.06), 3)

            driver = Sofor(
                ad_soyad=DRIVER_NAMES[i],
                telefon=f"05{random.randint(30, 59)}{random.randint(1000000, 9999999)}",
                ehliyet_sinifi="E",
                score=score,
                manual_score=round(
                    np.clip(score + random.uniform(-0.05, 0.05), 0.85, 1.20), 3
                ),
                hiz_disiplin_skoru=hiz_skor,
                agresif_surus_faktoru=agresif,
                ramp_skoru=ramp_skoru,
                istikrar_skoru=istikrar,
                aktif=True,
            )
            session.add(driver)
            drivers.append(driver)

        # ── 3. Vehicles (Araçlar) ──
        vehicles = []
        plates_used = set()
        for i in range(VEHICLE_COUNT):
            arch = VEHICLE_ARCHETYPES[i % len(VEHICLE_ARCHETYPES)]
            # Generate unique plate
            city_code = random.choice([34, 6, 16, 41, 35, 1, 33, 42, 27, 7])
            while True:
                plate = f"{city_code:02d} LOJ {random.randint(100, 999)}"
                if plate not in plates_used:
                    plates_used.add(plate)
                    break

            vehicle = Arac(
                plaka=plate,
                marka=arch["marka"],
                model=arch["model"],
                yil=arch["yil"] - random.randint(0, 2),  # Some variation
                tank_kapasitesi=arch["tank"],
                hedef_tuketim=32.0,
                bos_agirlik_kg=arch["bos_kg"],
                hava_direnc_katsayisi=arch["cd"],
                on_kesit_alani_m2=arch["area"],
                motor_verimliligi=arch["eff"],
                lastik_direnc_katsayisi=round(random.uniform(0.006, 0.008), 4),
                maks_yuk_kapasitesi_kg=26000,
                aktif=True,
            )
            session.add(vehicle)
            vehicles.append(vehicle)

        await session.commit()

        # Refresh to get IDs
        for r in master_routes:
            await session.refresh(r["entity"])
        for d in drivers:
            await session.refresh(d)
        for v in vehicles:
            await session.refresh(v)

        logger.info(
            f"✅ Created {len(master_routes)} routes, {len(drivers)} drivers, {len(vehicles)} vehicles."
        )
        return drivers, vehicles, master_routes


async def synthesize_trips(
    drivers: List,
    vehicles: List,
    master_routes: List,
) -> None:
    """Generate 20,000 trips with physics-based fuel consumption."""
    logger.info("╔════════════════════════════════════════╗")
    logger.info("║  SYNTHESIZING 20,000 TRIPS             ║")
    logger.info("╚════════════════════════════════════════╝")

    # physics = PhysicsBasedFuelPredictor() # Refined loop uses v_physics below
    total_trips = 0
    total_fuels = 0
    sefer_no_counter = 1

    # Time span
    total_days = (END_DATE - START_DATE).days

    async with AsyncSessionLocal() as session:
        batch_trips: List[Sefer] = []
        batch_fuels: List[YakitAlimi] = []

        for vi, v in enumerate(vehicles):
            # Vehicle-specific physics specs
            v_specs = VehicleSpecs(
                empty_weight_kg=v.bos_agirlik_kg,
                drag_coefficient=v.hava_direnc_katsayisi,
                frontal_area_m2=v.on_kesit_alani_m2,
                rolling_resistance=v.lastik_direnc_katsayisi,
                engine_efficiency=v.motor_verimliligi,
            )
            v_physics = PhysicsBasedFuelPredictor(vehicle=v_specs)
            v_age_factor = get_vehicle_age_factor(v.yil)

            current_km = random.randint(80000, 250000)
            fuel_in_tank = float(v.tank_kapasitesi) * random.uniform(0.6, 0.9)

            # Initial fueling
            init_date = START_DATE + timedelta(days=random.randint(0, 5))
            batch_fuels.append(
                YakitAlimi(
                    arac_id=v.id,
                    tarih=init_date.date(),
                    istasyon=random.choice(FUEL_STATIONS),
                    litre=Decimal(str(round(fuel_in_tank, 2))),
                    fiyat_tl=Decimal(str(round(random.uniform(42.0, 48.0), 2))),
                    toplam_tutar=Decimal(
                        str(round(fuel_in_tank * random.uniform(42, 48), 2))
                    ),
                    km_sayac=current_km,
                    depo_durumu="Dolu",
                    durum="Onaylandi",
                )
            )

            # Generate trips for this vehicle
            for t_idx in range(TRIPS_PER_VEHICLE):
                # Assign driver and route
                driver = random.choice(drivers)
                m_route = random.choice(master_routes)
                arch = m_route["arch"]
                lok = m_route["entity"]

                # Trip date spread across the time range
                trip_offset_days = int(
                    (t_idx / TRIPS_PER_VEHICLE) * total_days
                ) + random.randint(-2, 2)
                trip_offset_days = max(0, min(trip_offset_days, total_days))
                trip_date = START_DATE + timedelta(days=trip_offset_days)
                trip_hour = f"{random.randint(4, 20):02d}:{random.choice(['00', '15', '30', '45'])}"

                # Route jitter (±2%)
                mesafe = arch["mesafe"] * random.uniform(0.98, 1.02)
                ascent = arch["ascent"] * random.uniform(0.95, 1.05)
                descent = arch["descent"] * random.uniform(0.95, 1.05)

                # Load variation
                is_empty = random.random() < 0.12  # 12% empty trips
                if is_empty:
                    load_ton = 0.0
                    bos_kg = int(v.bos_agirlik_kg)
                    dolu_kg = bos_kg
                else:
                    load_ton = round(random.uniform(5, 26), 1)
                    bos_kg = int(v.bos_agirlik_kg)
                    dolu_kg = bos_kg + int(load_ton * 1000)

                net_kg = dolu_kg - bos_kg

                # ── Grade Distribution Jitter (Phase 5A Expert Refinement) ──
                # Instead of fixed ratios, we add noise to prevent ML from learning exact thresholds
                analysis = arch["road_analysis"]
                total_up_down = 0.0
                g_km, m_km, s_km = 0.0, 0.0, 0.0

                for cat_name, cat in analysis.items():
                    if cat_name in ("highway", "other"):
                        continue
                    updown = float(cat.get("up", 0)) + float(cat.get("down", 0))
                    total_up_down += updown
                    if cat_name in ("motorway", "trunk"):
                        g_km += updown
                    elif cat_name == "primary":
                        m_km += updown * random.uniform(0.65, 0.75)  # Moderate noise
                        g_km += updown * (1 - (m_km / updown if updown > 0 else 1))
                    else:
                        s_km += updown * random.uniform(0.45, 0.55)  # Steep noise
                        m_km += updown * random.uniform(0.25, 0.35)
                        g_km += updown - (s_km + m_km)

                total_graded = (mesafe * 0.65) + total_up_down  # 65% flat avg
                grade_gentle = (
                    min(1.0, (mesafe * 0.65 + g_km) / total_graded)
                    if total_graded > 0
                    else 1.0
                )
                grade_moderate = (
                    min(1.0, m_km / total_graded) if total_graded > 0 else 0.0
                )
                grade_steep = min(1.0, s_km / total_graded) if total_graded > 0 else 0.0

                # ── Route Fatigue & Stop-Go (Expert Refinement) ──
                # avg speed varies by road type
                avg_speed = 75.0 if arch["otoban_pct"] > 0.7 else 60.0
                avg_speed *= random.uniform(0.9, 1.1)
                duration_m = (mesafe / avg_speed) * 60.0

                # Stop-go cycles: sqrt(mesafe) * residential_ratio proxy
                res_ratio = (
                    arch["road_analysis"].get("residential", {}).get("flat", 0)
                    / arch["mesafe"]
                )
                stopgo_cycles = res_ratio * math.sqrt(mesafe) * 8.0  # Refined scale

                # Physics prediction
                route_data = RouteConditions(
                    distance_km=float(mesafe),
                    load_ton=float(load_ton),
                    is_empty_trip=is_empty,
                    ascent_m=float(ascent),
                    descent_m=float(descent),
                    flat_distance_km=float(mesafe * 0.65),
                    grade_gentle_pct=grade_gentle,
                    grade_moderate_pct=grade_moderate,
                    grade_steep_pct=grade_steep,
                    stopgo_cycles_per_100km=stopgo_cycles,
                    motorway_ratio=arch["otoban_pct"],
                    avg_speed_kmh=avg_speed,
                )
                prediction = v_physics.predict(route_data)
                base_l_100 = prediction.consumption_l_100km

                # Apply factors
                driver_impact = 1 + (driver.score - 1) * arch.get("sensitivity", 1.0)
                seasonal = get_seasonal_factor(trip_date.date())
                noise = np.random.normal(0, 0.012)  # ±1.2% noise

                actual_l_100 = (
                    base_l_100 * driver_impact * v_age_factor * seasonal * (1 + noise)
                )
                # Apply extra driver consistency jitter
                actual_l_100 *= 1 + (driver.istikrar_skoru - 1) * 0.2

                actual_l_100 = max(actual_l_100, 18.0)  # Floor
                actual_l_100 = min(actual_l_100, 55.0)  # Cap

                consumed_liters = (actual_l_100 * mesafe) / 100.0

                # Road metrics
                otoban_km, sehir_ici_km, flat_km = calculate_road_metrics(arch, mesafe)

                # Update odometer
                current_km += int(mesafe)

                # Sefer no
                sefer_no = f"SEF-{sefer_no_counter:05d}"
                sefer_no_counter += 1

                trip = Sefer(
                    sefer_no=sefer_no,
                    tarih=trip_date.date(),
                    saat=trip_hour,
                    arac_id=v.id,
                    sofor_id=driver.id,
                    guzergah_id=lok.id,
                    cikis_yeri=lok.cikis_yeri,
                    varis_yeri=lok.varis_yeri,
                    mesafe_km=round(float(mesafe), 1),
                    baslangic_km=current_km - int(mesafe),
                    bitis_km=current_km,
                    bos_agirlik_kg=bos_kg,
                    dolu_agirlik_kg=dolu_kg,
                    net_kg=net_kg,
                    ton=float(load_ton),
                    bos_sefer=is_empty,
                    tuketim=round(actual_l_100, 2),
                    tahmini_tuketim=round(base_l_100, 2),
                    dagitilan_yakit=Decimal(str(round(consumed_liters, 2))),
                    ascent_m=round(float(ascent), 1),
                    descent_m=round(float(descent), 1),
                    flat_distance_km=round(flat_km, 1),
                    otoban_mesafe_km=round(otoban_km, 1),
                    sehir_ici_mesafe_km=round(sehir_ici_km, 1),
                    duration_min=int(duration_m),  # Refined Fatigue proxy
                    rota_detay=arch["road_analysis"],
                    durum="Tamam",
                    is_real=False,
                )
                batch_trips.append(trip)
                total_trips += 1

                # Fuel tracking
                fuel_in_tank -= consumed_liters
                if fuel_in_tank < 120:
                    refill = float(v.tank_kapasitesi) - fuel_in_tank
                    price = round(random.uniform(42.0, 48.0), 2)
                    batch_fuels.append(
                        YakitAlimi(
                            arac_id=v.id,
                            tarih=trip_date.date(),
                            istasyon=random.choice(FUEL_STATIONS),
                            litre=Decimal(str(round(refill, 2))),
                            fiyat_tl=Decimal(str(price)),
                            toplam_tutar=Decimal(str(round(refill * price, 2))),
                            km_sayac=current_km,
                            fis_no=f"FIS-{random.randint(100000, 999999)}",
                            depo_durumu="Dolu",
                            durum="Onaylandi",
                        )
                    )
                    fuel_in_tank = float(v.tank_kapasitesi)
                    total_fuels += 1

                # Batch flush
                if len(batch_trips) >= BATCH_SIZE:
                    session.add_all(batch_trips)
                    session.add_all(batch_fuels)
                    await session.commit()
                    logger.info(
                        f"  💾 Flushed batch: {total_trips} trips, {total_fuels} fuels"
                    )
                    batch_trips = []
                    batch_fuels = []

            logger.info(
                f"  🚛 Vehicle {vi + 1}/{VEHICLE_COUNT}: {v.plaka} — {TRIPS_PER_VEHICLE} trips generated"
            )

        # Final flush
        if batch_trips or batch_fuels:
            session.add_all(batch_trips)
            session.add_all(batch_fuels)
            await session.commit()

    logger.info(f"✅ Total: {total_trips} trips, {total_fuels} fuel records created.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════


async def main():
    logger.info("═" * 60)
    logger.info("  LOJINEXT ELITE DATA SYNTHESIS — 20K REALISTIC TRIPS")
    logger.info("═" * 60)

    # ── Migration Phase (Phase 5A) ──
    async with AsyncSessionLocal() as session:
        logger.info("🛠️ Running schema migrations...")
        try:
            await session.execute(
                text(
                    "ALTER TABLE soforler ADD COLUMN IF NOT EXISTS ramp_skoru FLOAT DEFAULT 1.0;"
                )
            )
            await session.execute(
                text(
                    "ALTER TABLE soforler ADD COLUMN IF NOT EXISTS istikrar_skoru FLOAT DEFAULT 1.0;"
                )
            )
            await session.execute(
                text(
                    "ALTER TABLE seferler ADD COLUMN IF NOT EXISTS duration_min INTEGER;"
                )
            )
            await session.commit()
            logger.info("✅ Schema migrations complete.")
        except Exception as e:
            logger.warning(f"⚠️ Migration warning (might already exist): {e}")
            await session.rollback()

    # Phase 1: Clear
    await clear_all_data()

    # Phase 2: Master Data
    drivers, vehicles, routes = await create_master_data()

    # Phase 3: Trips
    await synthesize_trips(drivers, vehicles, routes)

    logger.info("═" * 60)
    logger.info("  ✅ SYNTHESIS COMPLETE")
    logger.info(f"  Vehicles: {VEHICLE_COUNT}")
    logger.info(f"  Drivers: {DRIVER_COUNT}")
    logger.info(f"  Routes: {len(ROUTE_ARCHETYPES)}")
    logger.info(f"  Total Trips: {VEHICLE_COUNT * TRIPS_PER_VEHICLE}")
    logger.info("═" * 60)


if __name__ == "__main__":
    asyncio.run(main())
