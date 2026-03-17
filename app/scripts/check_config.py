"""
Config smoke testi.
- Prod ortamında kritik envlerin dolu olduğunu ve CORS/rate-limit kısıtlarının ihlal edilmediğini kontrol eder.
- Eksik/hatalı durumda exit code 1 ile çıkar.
"""

import os
import sys
from app.config import settings


def fail(msg: str) -> None:
    print(f"[CONFIG-ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    env = settings.ENVIRONMENT
    required = {
        "SECRET_KEY": settings.SECRET_KEY,
        "GROQ_API_KEY": settings.GROQ_API_KEY,
        "OPENROUTESERVICE_API_KEY": settings.OPENROUTESERVICE_API_KEY,
        "CELERY_BROKER_URL": settings.CELERY_BROKER_URL,
        "CELERY_RESULT_BACKEND": settings.CELERY_RESULT_BACKEND,
    }
    # HF_TOKEN prod'da zorunlu
    if env == "prod":
        required["HF_TOKEN"] = settings.HF_TOKEN

    missing = [k for k, v in required.items() if not v]
    if missing:
        fail(f"Kritik env eksik: {', '.join(missing)} (ENVIRONMENT={env})")

    # CORS kontrolü
    if env == "prod":
        if not settings.CORS_ORIGINS:
            fail("CORS_ORIGINS boş olamaz (prod)")
        if "*" in settings.CORS_ORIGINS:
            fail("CORS_ORIGINS '*' içeremez (prod)")

    # Rate-limit başlık kontrolü (middleware yapılandırmasına dayanır)
    retry_after = os.getenv("RATE_LIMIT_RETRY_AFTER", "60")
    try:
        int(retry_after)
    except ValueError:
        fail("RATE_LIMIT_RETRY_AFTER sayısal olmalı")

    print(f"[CONFIG-OK] ENV={env}, kritik env değişkenleri mevcut.")


if __name__ == "__main__":
    main()
