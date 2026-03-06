"""
TIR Yakıt Takip Sistemi - Konfigürasyon
Modernized with pydantic-settings
"""

from pathlib import Path
from typing import List, Optional, Union

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Yollar
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

# Veritabanı dizinini oluştur (data files için)
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """
    Uygulama Ayarları
    Environment variable'lardan okunur ve validasyon yapılır.
    """

    # Uygulama Bilgileri
    APP_NAME: str = "TIR Yakıt Takip Sistemi"
    APP_VERSION: str = "2.0.0"
    APP_AUTHOR: str = "DevAI"
    API_V1_STR: str = "/api/v1"
    MAX_PAGINATION_LIMIT: int = 1000  # Pagination DoS koruması

    # Security - MUST be set in .env file
    ENVIRONMENT: str = "dev"  # dev, prod, test
    SECRET_KEY: SecretStr  # REQUIRED - repr()'da gizlenir
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ADMIN_PASSWORD: SecretStr  # Seed Admin Şifresi (Kullanıcı Tablosu İçin)
    SUPER_ADMIN_USERNAME: str = "skara"
    SUPER_ADMIN_PASSWORD: Optional[SecretStr] = (
        None  # Sadece .env'den okunur (bypass db)
    )

    # CORS
    # List of origins or comma-separated string
    CORS_ORIGINS: Union[List[str], str] = []

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return []

    @field_validator("CORS_ORIGINS", mode="after")
    def check_cors_and_warn(cls, v: List[str], info) -> List[str]:
        """Zero Tolerance: Prod ortamında '*' yasak. Dev ortamında boşsa uyar."""
        env = info.data.get("ENVIRONMENT", "dev")

        if env == "prod" and "*" in v:
            raise ValueError(
                "SECURITY RISK: CORS_ORIGINS cannot contain '*' in production environment"
            )

        if not v and env != "test":
            import logging

            logger = logging.getLogger("uvicorn")
            logger.warning(
                f"CORS_ORIGINS is empty in {env} mode. API might be inaccessible from web browsers."
            )

        return v

    @field_validator("ENVIRONMENT")
    def validate_env(cls, v: str) -> str:
        if v not in ["dev", "prod", "test"]:
            raise ValueError("ENVIRONMENT must be 'dev', 'prod' or 'test'")
        return v

    # Database
    DATABASE_URL: str
    ALEMBIC_READY: bool = False  # Set to True when migration setup is complete

    @property
    def masked_database_url(self) -> str:
        """Logging için credential'ları maskele"""
        import re

        return re.sub(r":([^:@]+)@", ":***@", self.DATABASE_URL)

    # External APIs
    OPENROUTESERVICE_API_KEY: str
    MAPBOX_API_KEY: Optional[str] = None
    ROUTING_PROVIDER_STRATEGY: str = "hybrid"  # or 'ors_only', 'mapbox_only'

    # AI Configuration
    AI_PROVIDER: str = "groq"
    GROQ_API_KEY: Optional[SecretStr] = None
    GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"
    AI_TEMPERATURE: float = 0.1
    AI_MAX_TOKENS: int = 1500

    # Defaults - Genel
    DEFAULT_FILO_HEDEF_TUKETIM: float = 32.0
    DEFAULT_ANORMAL_UST_SINIR: float = 45.0
    DEFAULT_ANORMAL_ALT_SINIR: float = 20.0

    # Analiz Servisi Ayarları
    ANOMALY_Z_THRESHOLD: float = 2.5  # Z-Score eşik değeri
    ELITE_SCORE_TRIP_LIMIT: int = 20  # Elite puanlama için max sefer sayısı

    # Tahmin Servisi Ayarları
    VEHICLE_AGE_DEGRADATION_RATE: float = 0.015  # Yıl başına verimlilik kaybı (%1.5)
    MAX_AGE_DEGRADATION: float = 0.15  # Maksimum yaş degradasyonu (%15)
    DEFAULT_LOAD_TON: float = 24.0  # Standart yüklü TIR tonajı

    # HGV Route Parametreleri
    HGV_AXLE_LOAD: float = 11.5  # ton
    HGV_GROSS_WEIGHT: float = 40.0  # ton
    HGV_HEIGHT: float = 4.0  # metre
    HGV_WEIGHT: float = 40.0  # ton
    HGV_LENGTH: float = 16.5  # metre
    HGV_EMPTY_WEIGHT: float = 14.5  # ton (boş TIR ağırlığı)

    # Rate Limiting Ayarları
    OPENROUTE_RATE_LIMIT: float = 2.0  # req/sec
    WEATHER_RATE_LIMIT: float = 5.0  # req/sec
    EXTERNAL_API_RATE_LIMIT: float = 10.0  # req/sec (generic)

    # Circuit Breaker Ayarları
    CB_FAIL_MAX: int = 5  # Hata sayısı
    CB_RESET_TIMEOUT: int = 60  # saniye

    # Weather Thresholds (weather_service.py'den taşındı)
    WEATHER_TEMP_HIGH_THRESHOLD: float = 35.0  # °C
    WEATHER_TEMP_LOW_THRESHOLD: float = -5.0  # °C
    WEATHER_WIND_HIGH_THRESHOLD: float = 50.0  # km/h
    WEATHER_IMPACT_HIGH: float = 1.15  # +15% yakıt etkisi
    WEATHER_IMPACT_MEDIUM: float = 1.05  # +5% yakıt etkisi

    # Logging & Security PII Masking
    LOG_PII_MASK_EMAIL: str = r"\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Z|a-z]{2,}\b"
    LOG_PII_MASK_PHONE: str = r"\b(?:\+90|0)?5\d{9}\b"
    LOG_PII_MASK_TCKN: str = r"\b\d{11}\b"
    LOG_PII_SENSITIVE_KEYS: List[str] = [
        "password",
        "passwd",
        "sifre",
        "secret",
        "token",
        "api_key",
        "apikey",
        "bearer",
        "auth",
        "credential",
        "jwt",
        "session_id",
    ]

    # Observability (Sentry & Prometheus)
    SENTRY_DSN: Optional[str] = None
    ENABLE_PROMETHEUS_METRICS: bool = True
    SENTRY_PII_FILTER: bool = True

    # RAG Settings
    AI_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    AI_EMBEDDING_DIM: int = 1024
    AI_RAG_MAX_CHARS: int = 4000
    AI_RAG_THRESHOLD: float = 0.4
    AI_RAG_MAX_DOC_CHARS: int = 2000

    # Backup Strategy
    BACKUP_RETENTION_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=(
            str(BASE_DIR / ".env")
            if (BASE_DIR / ".env").exists()
            else str(BASE_DIR.parent / ".env")
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Global Settings Instance
# Try-catch block allows importing config even if env vars are missing (e.g. during simple tests or CI without full env)
# But strictly, for running the app, this should raise error.
try:
    settings = Settings()
except Exception as e:
    # Fallback for dev/test environment without proper .env
    # Only if we are not in production. In production this should fail.
    # We'll print a warning and let it crash if accessed.
    print(f"WARNING: Configuration validation failed: {e}")
    print("Using dummy values for build/test purposes only.")

    # Dummy creation for CI/Test
    # Note: This effectively bypasses safety in Dev if developer is lazy.
    # But strictly requested "Zero Tolerance" likely implies we should FAIL.
    # User said "100/100 Backend Sagligi". So we should FAIL if config is wrong.
    # However, to prevent breaking "read_file" or "import" during analysis, I will raise the error.
    # Actually, let's allow it to propagate, so the user knows Config is missing.
    raise e

# =============================================================================
# CONSTANTS (Visual & UI - Kept for ReportGenerator or Legacy UI)
# =============================================================================

# Tema Renkleri (Koyu Tema)
COLORS = {
    "bg_dark": "#1a1a2e",  # Ana arka plan
    "bg_card": "#16213e",  # Kart arka planı
    "bg_sidebar": "#0f3460",  # Sidebar
    "bg_input": "#1f4068",  # Input alanları
    "accent": "#e94560",  # Vurgu rengi (kırmızı)
    "accent_hover": "#ff6b6b",  # Hover
    "primary": "#4361ee",  # Birincil (mavi)
    "success": "#00d9a5",  # Yeşil
    "warning": "#ffc107",  # Sarı
    "danger": "#dc3545",  # Kırmızı
    "text": "#ffffff",  # Ana metin
    "text_secondary": "#a0a0a0",  # İkincil metin
    "border": "#2a4a6e",  # Kenarlık
}

# Font Ayarları
FONTS = {
    "title": ("Segoe UI", 24, "bold"),
    "subtitle": ("Segoe UI", 18, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "small": ("Segoe UI", 10),
    "button": ("Segoe UI", 12, "bold"),
}

# Varsayılan Parametreler (Legacy Dict Access Support)
DEFAULT_PARAMS = {
    "filo_hedef_tuketim": settings.DEFAULT_FILO_HEDEF_TUKETIM,
    "anormal_ust_sinir": settings.DEFAULT_ANORMAL_UST_SINIR,
    "anormal_alt_sinir": settings.DEFAULT_ANORMAL_ALT_SINIR,
    "uzun_periyot_esigi": 2000,
    "otomatik_yedekleme": True,
    "yedek_gunu": 30,
}

# Pencere Boyutları
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 220


def get_system_font() -> str:
    """Platforma göre uygun font yolunu döndür"""
    import platform

    system = platform.system()

    if system == "Windows":
        return "C:/Windows/Fonts/arial.ttf"
    elif system == "Darwin":  # macOS
        return "/System/Library/Fonts/Helvetica.ttc"
    else:  # Linux
        # Yaygın Linux font yollarını kontrol et
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        ]
        for p in paths:
            if Path(p).exists():
                return p
        return "Arial"


# Tablo Başlıkları
YAKIT_COLUMNS = [
    ("ID", 50),
    ("Tarih", 100),
    ("Plaka", 100),
    ("İstasyon", 150),
    ("Fiyat", 80),
    ("Litre", 80),
    ("Tutar", 100),
    ("KM", 100),
]

SEFER_COLUMNS = [
    ("ID", 50),
    ("Tarih", 100),
    ("Saat", 70),
    ("Plaka", 100),
    ("Şoför", 120),
    ("Çıkış", 120),
    ("Varış", 120),
    ("Mesafe", 80),
    ("Ton", 70),
]
