"""
TIR Yakıt Takip - Validation Utilities
Sefer ve yakıt girişi için doğrulama kuralları
"""

import html
import re
import unicodedata
from typing import Any, Dict, List, Union

from app.core.entities.models import SeferCreate, YakitAlimiCreate

# Common SQL Injection patterns
SQL_INJECTION_PATTERNS = [
    r"(?i)(union\s+select)",
    r"(?i)(waitfor\s+delay)",
    r"(?i)(drop\s+table)",
    r"(?i)(insert\s+into)",
    r"(?i)(delete\s+from)",
    r"(?i)(update\s+set)",
    r"(?i)(exec\(\s*)",
    r"(?i)(--)",
    r"(?i)(\/\*)",
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",  # Unix style: ../
    r"\.\.[/\\]",  # Both styles: ../ or ..\
    r"(?i)%2e%2e[/\\]",  # URL encoded
]


def sanitize_input(data: Union[str, Any]) -> Any:
    """
    Kapsamlı sanitizasyon ve güvenlik kontrolü.
    - HTML escape
    - Unicode normalization (NFKC)
    - Null byte kontrolü
    - Path traversal kontrolü
    - SQL Injection pattern check
    """
    if isinstance(data, str):
        # 1. Unicode Normalization (Trims and standardizes Turkish chars)
        data = unicodedata.normalize("NFKC", data.strip())

        # 2. Null byte kontrolü (injection önlemi)
        if "\x00" in data:
            raise ValueError("Güvenlik ihlali: Geçersiz karakter tespit edildi")

        # 3. Path traversal kontrolü
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, data):
                raise ValueError(
                    "Güvenlik ihlali: Geçersiz karakter dizisi tespit edildi"
                )

        # 4. SQL Injection kontrolü (pattern sızdırmadan)
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, data):
                raise ValueError(
                    "Güvenlik ihlali: Geçersiz karakter dizisi tespit edildi"
                )

        # 5. HTML Escape
        return html.escape(data)
    return data


class TripValidator:
    """
    Sefer girişi için doğrulama kuralları.
    Hem UI (soft validation) hem de Backend (hard validation) tarafında kullanılır.
    """

    @staticmethod
    def validate_trip(data: Dict[str, Any]) -> List[str]:
        """
        Zorunlu kuralları kontrol eder. Errors listesi döner.
        Pydantic modellerini kullanarak hard validation yapar.
        """
        errors = []

        # Sanitization
        sanitized_data = {k: sanitize_input(v) for k, v in data.items()}

        # Pydantic validation
        try:
            SeferCreate(**sanitized_data)
        except Exception as e:
            # Pydantic hatalarını okunabilir hale getir
            if hasattr(e, "errors"):
                for err in e.errors():
                    field = err.get("loc", [""])[0]
                    msg = err.get("msg", "Geçersiz veri")
                    errors.append(f"{field}: {msg}")
            else:
                errors.append(str(e))

        return errors

    @staticmethod
    def get_soft_warnings(data: dict) -> List[str]:
        """
        Kullanıcıyı uyaracak (ama engellemeyecek) durumlar.
        """
        warnings = []
        try:
            mesafe = float(data.get("mesafe_km", 1))
            litre = float(data.get("tuketim", 0))

            if mesafe > 0 and litre > 0:
                avg = (litre / mesafe) * 100
                if avg > 45:  # 45 Litre/100km (Tır için bile yüksek)
                    warnings.append(
                        f"Dikkat: Ortalama tüketim çok yüksek ({avg:.1f} L/100km)."
                    )
                if avg < 20:  # 20 Litre altı (Tır için çok düşük)
                    warnings.append(
                        f"Dikkat: Tüketim şüpheli derecede düşük ({avg:.1f} L/100km)."
                    )
        except Exception:
            pass

        return warnings


class FuelValidator:
    """
    Yakıt alımı için doğrulama kuralları.
    """

    @staticmethod
    def validate_fuel_entry(data: Dict[str, Any]) -> List[str]:
        """
        Yakıt alımı için zorunlu kuralları kontrol eder.
        """
        errors = []

        # Sanitization
        sanitized_data = {k: sanitize_input(v) for k, v in data.items()}

        # Pydantic validation
        try:
            YakitAlimiCreate(**sanitized_data)
        except Exception as e:
            if hasattr(e, "errors"):
                for err in e.errors():
                    field = err.get("loc", [""])[0]
                    msg = err.get("msg", "Geçersiz veri")
                    errors.append(f"{field}: {msg}")
            else:
                errors.append(str(e))

        return errors
