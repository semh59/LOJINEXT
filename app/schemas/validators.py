"""
Pydantic Schemas için ortak güvenlik validatorları.

Bu modül tüm şemalarda kullanılacak güvenlik kontrollerini sağlar:
- XSS/HTML injection koruması
- Null byte koruması
- SQL injection karakterleri kontrolü
- Unicode normalizasyonu
"""

import re
import unicodedata
from typing import Any, Optional

from pydantic import field_validator


# Tehlikeli HTML/XSS pattern'leri
XSS_PATTERNS = [
    re.compile(r'<\s*script', re.IGNORECASE),
    re.compile(r'javascript\s*:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # onclick, onerror vb.
    re.compile(r'<\s*iframe', re.IGNORECASE),
    re.compile(r'<\s*object', re.IGNORECASE),
    re.compile(r'<\s*embed', re.IGNORECASE),
    re.compile(r'<\s*form', re.IGNORECASE),
    re.compile(r'<\s*style', re.IGNORECASE),
    re.compile(r'<\s*link', re.IGNORECASE),
    re.compile(r'<\s*meta', re.IGNORECASE),
    re.compile(r'<\s*svg', re.IGNORECASE),
    re.compile(r'<\s*math', re.IGNORECASE),
    re.compile(r'<\s*base', re.IGNORECASE),
    re.compile(r'data\s*:', re.IGNORECASE),
    re.compile(r'vbscript\s*:', re.IGNORECASE),
    re.compile(r'expression\s*\(', re.IGNORECASE),  # CSS expression
]

# Tehlikeli SQL karakterleri (basit kontrol, parameterized query asıl çözüm)
SQL_DANGEROUS_PATTERNS = [
    re.compile(r";\s*--", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s*'", re.IGNORECASE),
    re.compile(r"UNION\s+SELECT", re.IGNORECASE),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM", re.IGNORECASE),
    re.compile(r"INSERT\s+INTO", re.IGNORECASE),
]

# Alfanumerik + alt çizgi pattern (username için)
ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')

# Türkçe karakterlerle birlikte alfanumerik (isim için)
TURKISH_NAME_PATTERN = re.compile(r'^[a-zA-ZğüşöçıİĞÜŞÖÇ\s\-\.]+$')


def sanitize_string(value: str) -> str:
    """
    String değeri güvenli hale getirir.
    
    - Null byte temizleme
    - Unicode normalizasyonu (NFC)
    - Whitespace strip
    - Control karakterleri temizleme
    """
    if not isinstance(value, str):
        return value
    
    # Null byte temizle
    value = value.replace('\x00', '')
    
    # Unicode normalleştir (NFC - Canonical Decomposition, followed by Canonical Composition)
    value = unicodedata.normalize('NFC', value)
    
    # Control karakterleri temizle (newline, tab hariç)
    value = ''.join(
        char for char in value 
        if not unicodedata.category(char).startswith('C') 
        or char in '\n\r\t'
    )
    
    # Whitespace strip
    value = value.strip()
    
    return value


def check_xss(value: str) -> str:
    """
    XSS/HTML injection kontrolü yapar.
    Tehlikeli pattern bulunursa ValueError fırlatır.
    """
    if not isinstance(value, str):
        return value
    
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Potansiyel XSS içeriği tespit edildi: {pattern.pattern}")
    
    return value


def check_sql_injection(value: str) -> str:
    """
    SQL injection pattern kontrolü yapar.
    Tehlikeli pattern bulunursa ValueError fırlatır.
    
    NOT: Bu ek bir güvenlik katmanıdır. Asıl koruma parameterized query kullanımıdır.
    """
    if not isinstance(value, str):
        return value
    
    for pattern in SQL_DANGEROUS_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Potansiyel SQL injection içeriği tespit edildi")
    
    return value


def validate_safe_string(value: Optional[str]) -> Optional[str]:
    """
    Tam güvenlik validasyonu uygular:
    1. Sanitize
    2. XSS kontrolü
    3. SQL injection kontrolü
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        return value
    
    # Sanitize
    value = sanitize_string(value)
    
    # XSS kontrolü
    value = check_xss(value)
    
    # SQL kontrolü
    value = check_sql_injection(value)
    
    return value


def validate_username(value: str) -> str:
    """
    Kullanıcı adı validasyonu.
    Sadece alfanumerik ve alt çizgi kabul eder.
    """
    if not isinstance(value, str):
        return value
    
    value = sanitize_string(value)
    
    if not ALPHANUMERIC_PATTERN.match(value):
        raise ValueError(
            "Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir"
        )
    
    return value


def validate_name(value: str) -> str:
    """
    İsim validasyonu (ad_soyad gibi).
    Türkçe karakterler, boşluk, tire ve nokta kabul eder.
    """
    if not isinstance(value, str):
        return value
    
    value = sanitize_string(value)
    
    if not TURKISH_NAME_PATTERN.match(value):
        raise ValueError(
            "İsim sadece harf, boşluk, tire ve nokta içerebilir"
        )
    
    return value


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """
    Telefon numarasını maskeler.
    Örnek: 0532 123 45 67 -> 0532 *** ** 67
    """
    if not phone:
        return phone
    
    # Sadece rakamları al
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) < 4:
        return phone
    
    # İlk 4 ve son 2 rakamı göster, gerisini maskele
    return f"{digits[:4]} *** ** {digits[-2:]}"


def validate_dict_size(value: Optional[dict], max_keys: int = 100) -> Optional[dict]:
    """
    Dict boyutu kontrolü (DoS koruması).
    """
    if value is None:
        return None
    
    if not isinstance(value, dict):
        return value
    
    if len(value) > max_keys:
        raise ValueError(f"Dict en fazla {max_keys} anahtar içerebilir")
    
    return value


# Validator factory fonksiyonları - Pydantic field_validator ile kullanım için

def create_safe_string_validator(*fields: str):
    """SafeString validator oluşturur."""
    @field_validator(*fields, mode='before')
    @classmethod
    def validate_safe(cls, v: Optional[str]) -> Optional[str]:
        return validate_safe_string(v)
    return validate_safe


def create_username_validator(*fields: str):
    """Username validator oluşturur."""
    @field_validator(*fields, mode='before')
    @classmethod
    def validate_user(cls, v: str) -> str:
        return validate_username(v)
    return validate_user


def create_name_validator(*fields: str):
    """Name validator oluşturur."""
    @field_validator(*fields, mode='before')
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        return validate_name(v)
    return validate_name_field
