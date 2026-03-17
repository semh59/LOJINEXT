"""Canonical Sefer status contract and normalization helpers."""

from __future__ import annotations

import unicodedata
from typing import Dict, Final, Optional, Tuple

SEFER_STATUS_BEKLIYOR: Final = "Bekliyor"
SEFER_STATUS_PLANLANDI: Final = "Planlandı"
SEFER_STATUS_YOLDA: Final = "Yolda"
SEFER_STATUS_DEVAM_EDIYOR: Final = "Devam Ediyor"
SEFER_STATUS_TAMAMLANDI: Final = "Tamamlandı"
SEFER_STATUS_TAMAM: Final = "Tamam"
SEFER_STATUS_IPTAL: Final = "İptal"

CANONICAL_SEFER_STATUSES: Final[Tuple[str, ...]] = (
    SEFER_STATUS_BEKLIYOR,
    SEFER_STATUS_PLANLANDI,
    SEFER_STATUS_YOLDA,
    SEFER_STATUS_DEVAM_EDIYOR,
    SEFER_STATUS_TAMAMLANDI,
    SEFER_STATUS_TAMAM,
    SEFER_STATUS_IPTAL,
)
CANONICAL_SEFER_STATUS_SET: Final[set[str]] = set(CANONICAL_SEFER_STATUSES)

SEFER_STATUS_TRANSITIONS: Final[Dict[str, Tuple[str, ...]]] = {
    SEFER_STATUS_BEKLIYOR: (
        SEFER_STATUS_YOLDA,
        SEFER_STATUS_DEVAM_EDIYOR,
        SEFER_STATUS_IPTAL,
        SEFER_STATUS_PLANLANDI,
    ),
    SEFER_STATUS_PLANLANDI: (
        SEFER_STATUS_YOLDA,
        SEFER_STATUS_DEVAM_EDIYOR,
        SEFER_STATUS_IPTAL,
        SEFER_STATUS_BEKLIYOR,
    ),
    SEFER_STATUS_YOLDA: (
        SEFER_STATUS_TAMAMLANDI,
        SEFER_STATUS_TAMAM,
        SEFER_STATUS_IPTAL,
    ),
    SEFER_STATUS_DEVAM_EDIYOR: (
        SEFER_STATUS_TAMAMLANDI,
        SEFER_STATUS_TAMAM,
        SEFER_STATUS_IPTAL,
    ),
    SEFER_STATUS_TAMAMLANDI: (),
    SEFER_STATUS_TAMAM: (),
    SEFER_STATUS_IPTAL: (),
}

_LEGACY_STATUS_ALIASES: Final[Dict[str, str]] = {
    "Iptal": SEFER_STATUS_IPTAL,
    "IPTAL": SEFER_STATUS_IPTAL,
    "iptal": SEFER_STATUS_IPTAL,
    "Planlandi": SEFER_STATUS_PLANLANDI,
    "PLANLANDI": SEFER_STATUS_PLANLANDI,
    "planlandi": SEFER_STATUS_PLANLANDI,
    "Tamamlandi": SEFER_STATUS_TAMAMLANDI,
    "TAMAMLANDI": SEFER_STATUS_TAMAMLANDI,
    "tamamlandi": SEFER_STATUS_TAMAMLANDI,
    "PlanlandÄ±": SEFER_STATUS_PLANLANDI,  # Legacy mojibake
    "TamamlandÄ±": SEFER_STATUS_TAMAMLANDI,  # Legacy mojibake
    "Ä°ptal": SEFER_STATUS_IPTAL,  # Legacy mojibake
}


def _fold_status(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return "".join(ascii_only.casefold().split())


_FOLDED_STATUS_MAP: Final[Dict[str, str]] = {
    _fold_status(status): status for status in CANONICAL_SEFER_STATUSES
}
for legacy_value, canonical_value in _LEGACY_STATUS_ALIASES.items():
    _FOLDED_STATUS_MAP[_fold_status(legacy_value)] = canonical_value


def normalize_sefer_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    raw = str(value).strip()
    if not raw:
        return raw

    if raw in CANONICAL_SEFER_STATUS_SET:
        return raw

    return _FOLDED_STATUS_MAP.get(_fold_status(raw), raw)


def ensure_canonical_sefer_status(
    value: Optional[str], *, field_name: str = "durum", allow_none: bool = True
) -> Optional[str]:
    normalized = normalize_sefer_status(value)

    if normalized is None:
        if allow_none:
            return None
        raise ValueError(f"{field_name} zorunludur.")

    if normalized not in CANONICAL_SEFER_STATUS_SET:
        allowed = ", ".join(CANONICAL_SEFER_STATUSES)
        raise ValueError(
            f"Gecersiz {field_name}: '{value}'. Gecerli degerler: {allowed}"
        )

    return normalized
