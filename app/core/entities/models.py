"""
TIR Yakıt Takip Sistemi - Pydantic Entities
Type-safe veri modelleri
"""

import re
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class DurumEnum(str, Enum):
    """Kayıt durumu"""
    BEKLIYOR = "Bekliyor"
    TAMAM = "Tamam"
    HATA = "Hata"
    IPTAL = "İptal"
    PLANLANDI = "Planlandı"
    YOLDA = "Yolda"
    DEVAM_EDIYOR = "Devam Ediyor"


class ZorlukEnum(str, Enum):
    """Güzergah zorluğu"""
    KOLAY = "Kolay"
    NORMAL = "Normal"
    ZOR = "Zor"


class SeverityEnum(str, Enum):
    """Anomali şiddeti"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ============== BASE ENTITY ==============

class BaseEntity(BaseModel):
    """Tüm entity'ler için ortak base"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


# ============== ARAÇ ==============

class Arac(BaseEntity):
    """Araç entity'si - tam validation ile"""
    plaka: str = Field(..., min_length=7, max_length=12)
    marka: str = Field(..., min_length=2, max_length=50)
    model: Optional[str] = Field(default=None, max_length=50)
    yil: int = Field(ge=1990, le=2030)
    tank_kapasitesi: int = Field(default=600, ge=100, le=2000)
    hedef_tuketim: float = Field(default=32.0, ge=15.0, le=60.0)
    
    # Elite Technical Specs
    bos_agirlik_kg: float = Field(default=8000.0, ge=2000.0, le=15000.0)
    hava_direnc_katsayisi: float = Field(default=0.7, ge=0.3, le=1.2)
    on_kesit_alani_m2: float = Field(default=8.5, ge=4.0, le=12.0)
    motor_verimliligi: float = Field(default=0.38, ge=0.2, le=0.55)
    lastik_direnc_katsayisi: float = Field(default=0.007, ge=0.004, le=0.015)
    maks_yuk_kapasitesi_kg: int = Field(default=26000, ge=1000, le=40000)
    
    aktif: bool = True
    notlar: Optional[str] = Field(default=None, max_length=2000)

    @computed_field
    @property
    def yas(self) -> int:
        """Araç yaşı (yıl bazında) - dinamik hesaplama"""
        return date.today().year - self.yil

    @computed_field
    @property
    def euro_sinifi(self) -> str:
        """
        Euro emisyon sınıfı tahmini.
        Eski araçlar daha fazla yakıt harcar.
        """
        if self.yil >= 2014:
            return "Euro 6"
        elif self.yil >= 2009:
            return "Euro 5"
        elif self.yil >= 2006:
            return "Euro 4"
        return "Euro 3"

    @computed_field
    @property
    def yas_faktoru(self) -> float:
        """
        Araç yaşına göre yakıt tüketim faktörü.
        Yeni araç = 1.0, her 5 yıl için +%2 artış
        """
        base = 1.0
        yas = self.yas
        if yas <= 2:
            return 0.98  # Yeni araç avantajı
        elif yas <= 5:
            return 1.0
        elif yas <= 10:
            return 1.02 + (yas - 5) * 0.005  # 1.02 - 1.045
        else:
            return 1.05 + (yas - 10) * 0.01  # 1.05+ (max ~1.15)

    @field_validator('plaka')
    @classmethod
    def validate_plaka(cls, v: str) -> str:
        """Plaka formatını doğrula ve standardize et"""
        if not v:
            raise ValueError('Plaka boş olamaz')
        return validate_plaka_str(v)


# Helper validator function for plaka
def validate_plaka_str(v: str) -> str:
    v = v.upper().strip()
    v = ' '.join(v.split()) # Normalize spaces
    pattern = r'^(\d{2})\s*([A-Z]{1})\s*(\d{4})$|^(\d{2})\s*([A-Z]{2})\s*(\d{3,4})$|^(\d{2})\s*([A-Z]{3,4})\s*(\d{2,3})$'
    match = re.match(pattern, v)
    if not match:
        basic_pattern = r'^(\d{2})\s*([A-Z]{1,3})\s*(\d{2,4})$'
        if not re.match(basic_pattern, v):
             raise ValueError(f'Geçersiz plaka formatı: {v}')
        return v
    parts = [g for g in match.groups() if g]
    return f"{parts[0]} {parts[1]} {parts[2]}"

class AracCreate(BaseModel):
    """Araç oluşturma DTO"""
    plaka: str
    marka: str
    model: Optional[str] = None
    yil: int = 2020
    tank_kapasitesi: int = 600
    hedef_tuketim: float = 32.0
    
    # Optional elite specs for creation
    bos_agirlik_kg: Optional[float] = 8000.0
    hava_direnc_katsayisi: Optional[float] = 0.7
    on_kesit_alani_m2: Optional[float] = 8.5
    motor_verimliligi: Optional[float] = 0.38
    lastik_direnc_katsayisi: Optional[float] = 0.007
    maks_yuk_kapasitesi_kg: Optional[int] = 26000
    
    notlar: Optional[str] = None

    @field_validator('plaka')
    @classmethod
    def validate_plaka(cls, v: str) -> str:
        return validate_plaka_str(v)

    @field_validator('yil')
    @classmethod
    def validate_yil(cls, v: int) -> int:
        if v < 1980 or v > date.today().year + 1:
            raise ValueError('Geçersiz model yılı')
        return v


class AracUpdate(BaseModel):
    """Araç güncelleme DTO"""
    plaka: Optional[str] = None
    marka: Optional[str] = None
    model: Optional[str] = None
    yil: Optional[int] = None
    tank_kapasitesi: Optional[int] = None
    hedef_tuketim: Optional[float] = None
    aktif: Optional[bool] = None
    notlar: Optional[str] = None

    @field_validator('plaka')
    @classmethod
    def validate_plaka(cls, v: str) -> str:
        if v is None: return v
        return validate_plaka_str(v)


# ============== ŞOFÖR ==============

class Sofor(BaseEntity):
    """Şoför entity'si"""
    ad_soyad: str = Field(..., min_length=3, max_length=100)
    telefon: Optional[str] = Field(default=None, max_length=20)
    ise_baslama: Optional[date] = None
    ehliyet_sinifi: str = Field(default="E", max_length=5)
    
    # Elite Behavioral Stats
    score: float = Field(default=1.0, ge=0.1, le=2.0)
    hiz_disiplin_skoru: float = Field(default=1.0, ge=0.5, le=1.5)
    agresif_surus_faktoru: float = Field(default=1.0, ge=0.5, le=1.5)
    
    aktif: bool = True
    notlar: Optional[str] = Field(default=None, max_length=2000)

    @field_validator('ad_soyad')
    @classmethod
    def validate_ad_soyad(cls, v: str) -> str:
        """Ad soyadı title case yap"""
        return ' '.join(word.capitalize() for word in v.strip().split())


class SoforCreate(BaseModel):
    """Şoför oluşturma DTO"""
    ad_soyad: str = Field(..., min_length=3)
    telefon: Optional[str] = None
    ise_baslama: Optional[date] = None
    ehliyet_sinifi: str = "E"
    notlar: Optional[str] = None

    @field_validator('ad_soyad')
    @classmethod
    def validate_ad_soyad(cls, v: str) -> str:
        return v.strip().title()


# ============== LOKASYON ==============

class Lokasyon(BaseEntity):
    """Lokasyon/güzergah entity'si"""
    cikis_yeri: str = Field(..., min_length=2, max_length=100)
    varis_yeri: str = Field(..., min_length=2, max_length=100)
    mesafe_km: int = Field(..., gt=0, le=5000)
    tahmini_sure_saat: Optional[float] = Field(default=None, ge=0, le=48)
    zorluk: ZorlukEnum = ZorlukEnum.NORMAL
    notlar: Optional[str] = Field(default=None, max_length=2000)

    @field_validator('cikis_yeri', 'varis_yeri')
    @classmethod
    def validate_yer(cls, v: str) -> str:
        return v.strip().title()


# ============== YAKIT ALIMI ==============

class YakitAlimi(BaseEntity):
    """Yakıt alımı entity'si"""
    tarih: date
    arac_id: int = Field(..., gt=0)
    istasyon: Optional[str] = Field(default=None, max_length=100)
    fiyat_tl: Decimal = Field(..., gt=Decimal("0"), le=Decimal("200"))
    litre: float = Field(..., gt=0, le=2000)
    km_sayac: int = Field(..., gt=0)
    fis_no: Optional[str] = Field(default=None, max_length=50)
    durum: DurumEnum = DurumEnum.BEKLIYOR

    # İlişkili veri (optional, JOIN'den gelir)
    plaka: Optional[str] = None

    @field_validator('fiyat_tl', mode='before')
    @classmethod
    def normalize_fiyat(cls, v: Any) -> Decimal:
        """Float değerleri Decimal'e çevirirken yuvarla"""
        if isinstance(v, float):
            # Float hassasiyet sorununu çözmek için string üzerinden çevir
            # Ancak önce yuvarla ki 41.050000001 gibi değerler 41.05 olsun
            return Decimal(f"{v:.2f}")
        return v

    @field_validator('fiyat_tl')
    @classmethod
    def validate_decimal_places(cls, v: Decimal) -> Decimal:
        """Fiyat en fazla 2 ondalık basamak içerebilir"""
        # Quantize to 2 decimal places to be safe
        return v.quantize(Decimal("0.01"))

    @computed_field
    @property
    def toplam_tutar(self) -> Decimal:
        """Toplam tutarı hesapla"""
        return round(self.fiyat_tl * Decimal(str(self.litre)), 2)


class YakitAlimiCreate(BaseModel):
    """Yakıt alımı oluşturma DTO"""
    tarih: date
    arac_id: int = Field(..., gt=0)
    istasyon: Optional[str] = Field(default=None, max_length=100)
    fiyat_tl: Decimal = Field(..., gt=Decimal("0"), le=Decimal("200"))
    litre: float = Field(..., gt=0, le=2000)
    km_sayac: int = Field(..., gt=0)
    fis_no: Optional[str] = Field(default=None, max_length=50)
    depo_durumu: Optional[str] = "Bilinmiyor"

    @field_validator('fiyat_tl', mode='before')
    @classmethod
    def normalize_fiyat(cls, v: Any) -> Decimal:
        if isinstance(v, float):
            return Decimal(f"{v:.2f}")
        return v

    @computed_field
    @property
    def toplam_tutar(self) -> Decimal:
        """Toplam tutarı hesapla"""
        return round(self.fiyat_tl * Decimal(str(self.litre)), 2)


# ============== SEFER ==============

class Sefer(BaseEntity):
    """Sefer entity'si"""
    tarih: date
    saat: Optional[str] = Field(default=None, max_length=5)
    # Foreign Keys
    guzergah_id: Optional[int] = None
    arac_id: int = Field(..., gt=0)
    sofor_id: int = Field(..., gt=0)
    periyot_id: Optional[int] = None
    
    # Weight Info
    bos_agirlik_kg: int = Field(default=0, ge=0)
    dolu_agirlik_kg: int = Field(default=0, ge=0)
    net_kg: int = Field(default=0, ge=0)
    
    cikis_yeri: str = Field(..., min_length=2)
    varis_yeri: str = Field(..., min_length=2)
    mesafe_km: int = Field(..., ge=0, le=5000)
    bos_sefer: bool = False
    durum: DurumEnum = DurumEnum.TAMAM

    # Hesaplanan alanlar
    dagitilan_yakit: Optional[float] = None
    tuketim: Optional[float] = None
    ascent_m: Optional[float] = None
    descent_m: Optional[float] = None

    # İlişkili veri (JOIN'den)
    plaka: Optional[str] = None
    sofor_adi: Optional[str] = None

    @computed_field
    @property
    def ton(self) -> float:
        """Net ağırlığı tona çevir"""
        return round(self.net_kg / 1000, 2)


class SeferCreate(BaseModel):
    """Sefer oluşturma DTO"""
    tarih: date
    saat: Optional[str] = None
    arac_id: int = Field(..., gt=0)
    sofor_id: int = Field(..., gt=0)
    guzergah_id: int = Field(..., gt=0)
    
    # Weight Info
    bos_agirlik_kg: int = Field(0, ge=0)
    dolu_agirlik_kg: int = Field(0, ge=0)
    net_kg: int = Field(0, ge=0)
    ton: float = Field(0.0, ge=0.0)
    
    cikis_yeri: str = Field(..., min_length=2)
    varis_yeri: str = Field(..., min_length=2)
    mesafe_km: int = Field(..., gt=0, le=5000)
    bos_sefer: bool = False
    ascent_m: float = 0.0
    descent_m: float = 0.0
    notlar: Optional[str] = None

    @field_validator('cikis_yeri', 'varis_yeri')
    @classmethod
    def validate_yer(cls, v: str) -> str:
         return v.strip().title()



# ============== YAKIT PERİYODU ==============

class YakitPeriyodu(BaseEntity):
    """İki yakıt alımı arası periyot"""
    arac_id: int
    alim1_id: int
    alim2_id: int
    alim1_tarih: date
    alim1_km: int
    alim1_litre: float
    alim2_tarih: date
    alim2_km: int

    # Hesaplanan
    ara_mesafe: int = 0
    toplam_yakit: float = 0.0
    ort_tuketim: float = 0.0
    sefer_sayisi: int = 0
    durum: Optional[str] = None

    @computed_field
    @property
    def gun_sayisi(self) -> int:
        """Periyot gün sayısı"""
        return (self.alim2_tarih - self.alim1_tarih).days


# ============== ANALİZ SONUÇLARI ==============

class AnomalyResult(BaseModel):
    """Anomali tespit sonucu"""
    index: int
    value: float
    z_score: float
    severity: SeverityEnum
    message: str = ""

    @computed_field
    @property
    def is_critical(self) -> bool:
        return self.severity in [SeverityEnum.HIGH, SeverityEnum.CRITICAL]


class VehicleStats(BaseModel):
    """Araç istatistikleri"""
    arac_id: int
    plaka: str
    toplam_sefer: int = 0
    toplam_km: int = 0
    toplam_yakit: float = 0.0
    ort_tuketim: float = 0.0
    en_iyi_tuketim: Optional[float] = None
    en_kotu_tuketim: Optional[float] = None
    anomali_sayisi: int = 0


class DriverStats(BaseModel):
    """Şoför istatistikleri - Genişletilmiş"""
    sofor_id: int
    ad_soyad: str

    # Temel metrikler
    toplam_sefer: int = 0
    toplam_km: int = 0
    toplam_ton: float = 0.0
    bos_sefer_sayisi: int = 0

    # Yakıt metrikleri
    toplam_yakit: float = 0.0
    ort_tuketim: float = 0.0
    en_iyi_tuketim: Optional[float] = None
    en_kotu_tuketim: Optional[float] = None

    # Performans
    filo_karsilastirma: float = 0.0  # % filo ortalamasına göre (+/- değer)
    performans_puani: Optional[float] = None    # 0-100 (None = Veri Yetersiz)
    trend: str = "stable"            # improving/stable/declining


    # Güzergah bazlı
    en_cok_gidilen_guzergah: Optional[str] = None
    guzergah_sayisi: int = 0


class DashboardStats(BaseModel):
    """Dashboard özet istatistikleri"""
    toplam_sefer: int = 0
    toplam_km: int = 0
    toplam_yakit: float = 0.0
    filo_ortalama: float = 0.0
    aktif_arac: int = 0
    aktif_sofor: int = 0
    bugun_sefer: int = 0


# ============== AYARLAR ==============

class Ayar(BaseModel):
    """Sistem ayarı"""
    anahtar: str
    deger: str
    aciklama: Optional[str] = None

    def as_float(self) -> float:
        return float(self.deger)

    def as_int(self) -> int:
        return int(self.deger)

    def as_bool(self) -> bool:
        return self.deger.lower() in ('1', 'true', 'yes', 'evet')


# ============== GÜZERGAH ==============

class Guzergah(BaseEntity):
    """Güzergah Entity"""
    ad: Optional[str] = Field(None, min_length=2, max_length=100)
    cikis_yeri: str = Field(..., min_length=2, max_length=100)
    varis_yeri: str = Field(..., min_length=2, max_length=100)
    mesafe_km: int = Field(..., gt=0)
    varsayilan_arac_id: Optional[int] = Field(None, gt=0)
    varsayilan_sofor_id: Optional[int] = Field(None, gt=0)
    notlar: Optional[str] = None
    aktif: bool = True

class GuzergahCreate(BaseModel):
    """Güzergah oluşturma DTO"""
    ad: Optional[str] = None
    cikis_yeri: str = Field(..., min_length=2)
    varis_yeri: str = Field(..., min_length=2)
    mesafe_km: int = Field(..., gt=0)
    varsayilan_arac_id: Optional[int] = None
    varsayilan_sofor_id: Optional[int] = None
    notlar: Optional[str] = None
