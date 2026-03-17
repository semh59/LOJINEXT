import enum
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    BigInteger,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY

# from geoalchemy2 import Geometry
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)


def get_utc_now(ctx=None, *args, **kwargs):
    return datetime.now(timezone.utc)


class BakimTipi(str, enum.Enum):
    PERIYODIK = "PERIYODIK"
    ARIZA = "ARIZA"
    ACIL = "ACIL"


class Base(AsyncAttrs, DeclarativeBase):
    # type_annotation_map = {
    #     Any: Geometry,
    # }
    pass


class Arac(Base):
    __tablename__ = "araclar"
    __table_args__ = (
        CheckConstraint("tank_kapasitesi > 0", name="check_tank_kapasitesi_positive"),
        Index("idx_arac_aktif", "aktif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plaka: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    marka: Mapped[str] = mapped_column(String(50))
    model: Mapped[Optional[str]] = mapped_column(String(50))
    yil: Mapped[Optional[int]] = mapped_column(Integer)
    tank_kapasitesi: Mapped[int] = mapped_column(
        Integer, server_default=text("600"), default=600
    )
    hedef_tuketim: Mapped[float] = mapped_column(
        Float, server_default=text("32.0"), default=32.0
    )
    muayene_tarihi: Mapped[Optional[date]] = mapped_column(Date)

    # Elite Technical Specs
    bos_agirlik_kg: Mapped[float] = mapped_column(
        Float, server_default=text("8000.0"), default=8000.0
    )
    hava_direnc_katsayisi: Mapped[float] = mapped_column(
        Float, server_default=text("0.7"), default=0.7
    )  # Cd
    on_kesit_alani_m2: Mapped[float] = mapped_column(
        Float, server_default=text("8.5"), default=8.5
    )  # Frontal Area
    motor_verimliligi: Mapped[float] = mapped_column(
        Float, server_default=text("0.38"), default=0.38
    )
    lastik_direnc_katsayisi: Mapped[float] = mapped_column(
        Float, server_default=text("0.007"), default=0.007
    )
    maks_yuk_kapasitesi_kg: Mapped[int] = mapped_column(
        Integer, server_default=text("26000"), default=26000
    )

    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    notlar: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=get_utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=get_utc_now,
    )

    # Relationships
    yakit_alimlari: Mapped[List["YakitAlimi"]] = relationship(
        back_populates="arac", cascade="all, delete-orphan"
    )
    bakimlar: Mapped[List["AracBakim"]] = relationship(
        back_populates="arac", cascade="all, delete-orphan"
    )
    seferler: Mapped[List["Sefer"]] = relationship(back_populates="arac")
    yakit_periyotlari: Mapped[List["YakitPeriyodu"]] = relationship(
        back_populates="arac"
    )
    formul: Mapped[Optional["YakitFormul"]] = relationship(
        back_populates="arac", uselist=False
    )
    event_logs: Mapped[List["VehicleEventLog"]] = relationship(
        back_populates="arac", cascade="all, delete-orphan"
    )


class Dorse(Base):
    __tablename__ = "dorseler"
    __table_args__ = (Index("idx_dorse_aktif", "aktif"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plaka: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    marka: Mapped[Optional[str]] = mapped_column(String(50))
    # Brandali, Frigorifik, Konteyner, Tanker vs.
    tipi: Mapped[str] = mapped_column(String(50), default="Standart")
    yil: Mapped[Optional[int]] = mapped_column(Integer)

    # Physics Metrics
    bos_agirlik_kg: Mapped[float] = mapped_column(
        Float, server_default=text("6000.0"), default=6000.0
    )
    maks_yuk_kapasitesi_kg: Mapped[int] = mapped_column(
        Integer, server_default=text("24000"), default=24000
    )
    lastik_sayisi: Mapped[int] = mapped_column(Integer, default=6)
    dorse_lastik_direnc_katsayisi: Mapped[float] = mapped_column(Float, default=0.006)
    dorse_hava_direnci: Mapped[float] = mapped_column(Float, default=0.2)

    muayene_tarihi: Mapped[Optional[date]] = mapped_column(Date)
    notlar: Mapped[Optional[str]] = mapped_column(Text)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=get_utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=get_utc_now,
    )

    # Relationships
    seferler: Mapped[List["Sefer"]] = relationship(back_populates="dorse")
    bakimlar: Mapped[List["AracBakim"]] = relationship(
        back_populates="dorse", cascade="all, delete-orphan"
    )


class Sofor(Base):
    __tablename__ = "soforler"
    __table_args__ = (
        Index("idx_sofor_aktif", "aktif"),
        Index("idx_sofor_is_deleted", "is_deleted"),
        CheckConstraint("score >= 0.1 AND score <= 2.0", name="chk_sofor_score_range"),
        CheckConstraint(
            "manual_score >= 0.1 AND manual_score <= 2.0",
            name="chk_sofor_manual_score_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ad_soyad: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    telefon: Mapped[Optional[str]] = mapped_column(String(20))
    ise_baslama: Mapped[Optional[date]] = mapped_column(Date)
    ehliyet_sinifi: Mapped[str] = mapped_column(String(10), default="E")

    # Elite Behavioral Stats
    score: Mapped[float] = mapped_column(
        Float, default=1.0
    )  # Driver performance score (0.1 - 2.0)
    manual_score: Mapped[float] = mapped_column(Float, default=1.0)  # Manual evaluation
    hiz_disiplin_skoru: Mapped[float] = mapped_column(Float, default=1.0)
    agresif_surus_faktoru: Mapped[float] = mapped_column(Float, default=1.0)
    # Phase 5A: Elite Driver Factors
    ramp_skoru: Mapped[float] = mapped_column(
        Float, default=1.0, server_default=text("1.0")
    )  # Slope behavior
    istikrar_skoru: Mapped[float] = mapped_column(
        Float, default=1.0, server_default=text("1.0")
    )  # Consistency

    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    notlar: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )

    # Relationships
    seferler: Mapped[List["Sefer"]] = relationship(back_populates="sofor")


class SoforAdaptasyon(Base):
    __tablename__ = "sofor_adaptasyon"

    id: Mapped[int] = mapped_column(primary_key=True)
    surucu_id: Mapped[int] = mapped_column(
        ForeignKey("soforler.id", ondelete="CASCADE"), unique=True, index=True
    )
    guvenlik_skoru: Mapped[float] = mapped_column(Float, default=100.0)
    verimlilik_skoru: Mapped[float] = mapped_column(Float, default=100.0)
    eco_driving_basarisi: Mapped[float] = mapped_column(Float, default=0.0)
    rutin_disi_davranis_orani: Mapped[float] = mapped_column(Float, default=0.0)
    son_degerlendirme_tarihi: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    onerilen_modul: Mapped[Optional[str]] = mapped_column(String(100))
    risk_kategorisi: Mapped[str] = mapped_column(String(50), default="Düşük")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class Lokasyon(Base):
    __tablename__ = "lokasyonlar"
    __table_args__ = (
        UniqueConstraint("cikis_yeri", "varis_yeri", name="uq_cikis_varis"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cikis_yeri: Mapped[str] = mapped_column(String(100))
    varis_yeri: Mapped[str] = mapped_column(String(100))
    mesafe_km: Mapped[float] = mapped_column(Float)
    tahmini_sure_saat: Mapped[Optional[float]] = mapped_column(Float)
    zorluk: Mapped[str] = mapped_column(String(20), default="Normal")

    # Coordinates
    cikis_lat: Mapped[Optional[float]] = mapped_column(Float)
    cikis_lon: Mapped[Optional[float]] = mapped_column(Float)
    varis_lat: Mapped[Optional[float]] = mapped_column(Float)
    varis_lon: Mapped[Optional[float]] = mapped_column(Float)

    # API Metrics
    api_mesafe_km: Mapped[Optional[float]] = mapped_column(Float)
    api_sure_saat: Mapped[Optional[float]] = mapped_column(Float)
    ascent_m: Mapped[Optional[float]] = mapped_column(Float)
    descent_m: Mapped[Optional[float]] = mapped_column(Float)
    flat_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    otoban_mesafe_km: Mapped[Optional[float]] = mapped_column(Float)
    sehir_ici_mesafe_km: Mapped[Optional[float]] = mapped_column(Float)
    tahmini_yakit_lt: Mapped[Optional[float]] = mapped_column(Float)
    last_api_call: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # PostGIS Spatial Data (Removed temporarily due to missing columns/extension)
    # cikis_geom: Mapped[Optional[Any]] = mapped_column(Geometry("POINT", srid=4326))
    # varis_geom: Mapped[Optional[Any]] = mapped_column(Geometry("POINT", srid=4326))
    # rota_geom: Mapped[Optional[Any]] = mapped_column(Geometry("LINESTRING", srid=4326))

    route_analysis: Mapped[Optional[dict]] = mapped_column(JSON)
    source: Mapped[Optional[str]] = mapped_column(String(50))
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    correction_reason: Mapped[Optional[str]] = mapped_column(Text)
    notlar: Mapped[Optional[str]] = mapped_column(Text)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    kalibrasyonlar: Mapped[List["GuzergahKalibrasyon"]] = relationship(
        back_populates="lokasyon", cascade="all, delete-orphan"
    )
    seferler: Mapped[List["Sefer"]] = relationship(back_populates="guzergah")


class YakitAlimi(Base):
    __tablename__ = "yakit_alimlari"
    __table_args__ = (
        Index("idx_yakit_arac_tarih", "arac_id", "tarih"),
        CheckConstraint("litre > 0", name="check_yakit_litre_positive"),
        CheckConstraint("fiyat_tl > 0", name="check_yakit_fiyat_positive"),
        Index("idx_yakit_aktif", "aktif"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tarih: Mapped[date] = mapped_column(Date, index=True)
    arac_id: Mapped[int] = mapped_column(
        ForeignKey("araclar.id", ondelete="RESTRICT"), index=True
    )
    istasyon: Mapped[Optional[str]] = mapped_column(String(100))
    fiyat_tl: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    litre: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    toplam_tutar: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    km_sayac: Mapped[int] = mapped_column(Integer)
    fis_no: Mapped[Optional[str]] = mapped_column(String(50))
    depo_durumu: Mapped[str] = mapped_column(String(20), default="Bilinmiyor")
    durum: Mapped[str] = mapped_column(
        String(20), default="Bekliyor"
    )  # Bekliyor, Onaylandi
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)  # Soft delete flag
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )
    # Relationships
    arac: Mapped["Arac"] = relationship(back_populates="yakit_alimlari")

    last_fetched: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Sefer(Base):
    __tablename__ = "seferler"
    __table_args__ = (
        Index("idx_seferler_durum_tarih", "durum", "tarih"),
        CheckConstraint("mesafe_km > 0", name="check_sefer_mesafe_positive"),
        CheckConstraint(
            "net_kg = dolu_agirlik_kg - bos_agirlik_kg", name="check_sefer_net_kg_calc"
        ),
        CheckConstraint("bos_agirlik_kg >= 0", name="check_sefer_bos_agirlik_positive"),
        CheckConstraint(
            "dolu_agirlik_kg >= 0", name="check_sefer_dolu_agirlik_positive"
        ),
        CheckConstraint("net_kg >= 0", name="check_sefer_net_kg_positive"),
        CheckConstraint(
            "durum IN ('Bekliyor', 'Planland\u0131', 'Yolda', 'Devam Ediyor', 'Tamamland\u0131', 'Tamam', '\u0130ptal')",
            name="check_sefer_durum_enum",
        ),
        Index("idx_seferler_rota_detay_gin", "rota_detay", postgresql_using="gin"),
        Index("idx_seferler_tahmin_meta_gin", "tahmin_meta", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sefer_no: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, index=True
    )  # Business Key (e.g. SEF-001)
    tarih: Mapped[date] = mapped_column(Date, index=True)
    saat: Mapped[Optional[str]] = mapped_column(String(5))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Foreign Keys
    guzergah_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lokasyonlar.id", ondelete="SET NULL"), index=True
    )
    arac_id: Mapped[int] = mapped_column(
        ForeignKey("araclar.id", ondelete="RESTRICT"), index=True
    )
    dorse_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("dorseler.id", ondelete="SET NULL"), index=True
    )
    sofor_id: Mapped[int] = mapped_column(
        ForeignKey("soforler.id", ondelete="RESTRICT"), index=True
    )
    periyot_id: Mapped[Optional[int]] = mapped_column(
        Integer, index=True
    )  # Soft link to periyot

    # Weight Info
    bos_agirlik_kg: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), default=0
    )
    dolu_agirlik_kg: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), default=0
    )
    net_kg: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), default=0
    )  # Computed: Dolu - Boş
    ton: Mapped[float] = mapped_column(
        Float, server_default=text("0.0"), default=0.0
    )  # Computed

    # Location Info
    cikis_yeri: Mapped[str] = mapped_column(String(100))
    varis_yeri: Mapped[str] = mapped_column(String(100))
    mesafe_km: Mapped[float] = mapped_column(Float)
    baslangic_km: Mapped[Optional[int]] = mapped_column(Integer)
    bitis_km: Mapped[Optional[int]] = mapped_column(Integer)

    # Trip Status & Details
    bos_sefer: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    durum: Mapped[str] = mapped_column(
        String(20), default="Tamam", server_default=text("'Tamam'")
    )
    notlar: Mapped[Optional[str]] = mapped_column(String(255))

    # Fuel & API Data
    dagitilan_yakit: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    tahmini_tuketim: Mapped[Optional[float]] = mapped_column(
        Float
    )  # AI predicted consumption
    tahmin_meta: Mapped[Optional[dict]] = mapped_column(JSON)
    rota_detay: Mapped[Optional[dict]] = mapped_column(JSON)  # Route path and details
    tuketim: Mapped[Optional[float]] = mapped_column(Float)
    ascent_m: Mapped[Optional[float]] = mapped_column(Float)
    descent_m: Mapped[Optional[float]] = mapped_column(Float)
    flat_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    otoban_mesafe_km: Mapped[Optional[float]] = mapped_column(Float)
    sehir_ici_mesafe_km: Mapped[Optional[float]] = mapped_column(Float)
    is_real: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Data Guarding: Synthetic vs Real
    duration_min: Mapped[Optional[int]] = mapped_column(
        Integer
    )  # Time proxy for fatigue

    # Audit Logs
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="SET NULL"), index=True
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="SET NULL"), index=True
    )
    iptal_nedeni: Mapped[Optional[str]] = mapped_column(String(255))
    # B-004: Optimistic Locking — her update'te version +1 artar
    version: Mapped[int] = mapped_column(
        Integer, default=1, server_default=text("1"), nullable=False
    )

    # PostGIS Spatial Data (Removed temporarily due to missing columns/extension)
    # cikis_geom: Mapped[Optional[Any]] = mapped_column(Geometry("POINT", srid=4326))
    # varis_geom: Mapped[Optional[Any]] = mapped_column(Geometry("POINT", srid=4326))

    # Meta
    # aktif: Mapped[bool] = mapped_column(Boolean, default=True)  # REMOVED - Hard Delete
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=get_utc_now,
    )

    # Relationships
    arac: Mapped["Arac"] = relationship(back_populates="seferler")
    dorse: Mapped[Optional["Dorse"]] = relationship(back_populates="seferler")
    sofor: Mapped["Sofor"] = relationship(back_populates="seferler")
    guzergah: Mapped[Optional["Lokasyon"]] = relationship(back_populates="seferler")
    created_by: Mapped[Optional["Kullanici"]] = relationship(
        foreign_keys=[created_by_id]
    )
    updated_by: Mapped[Optional["Kullanici"]] = relationship(
        foreign_keys=[updated_by_id]
    )

    @validates("mesafe_km")
    def validate_mesafe(self, key, value):
        if value is not None and value <= 0:
            raise ValueError(f"Mesafe (km) 0'dan büyük olmalıdır: {value}")
        return value

    @validates("net_kg")
    def validate_net_kg(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"Net ağırlık (kg) negatif olamaz: {value}")
        return value


class SeferLog(Base):
    __tablename__ = "seferler_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    sefer_id: Mapped[int] = mapped_column(
        ForeignKey("seferler.id", ondelete="CASCADE"), index=True
    )
    degisen_alan: Mapped[Optional[str]] = mapped_column(String(50))
    eski_deger: Mapped[Optional[str]] = mapped_column(String)
    yeni_deger: Mapped[Optional[str]] = mapped_column(String)
    degistiren_id: Mapped[Optional[int]] = mapped_column(Integer)
    islem_tipi: Mapped[str] = mapped_column(String(20))  # INSERT, UPDATE, DELETE
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    sefer: Mapped["Sefer"] = relationship()


class YakitPeriyodu(Base):
    __tablename__ = "yakit_periyotlari"
    __table_args__ = (
        UniqueConstraint("arac_id", "alim1_id", "alim2_id", name="uq_yakit_periyodu"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    arac_id: Mapped[int] = mapped_column(ForeignKey("araclar.id", ondelete="RESTRICT"))
    alim1_id: Mapped[int] = mapped_column(
        Integer
    )  # FK to YakitAlimi but handled manually or separate rel
    alim2_id: Mapped[int] = mapped_column(Integer)

    alim1_tarih: Mapped[Optional[date]] = mapped_column(Date)
    alim1_km: Mapped[Optional[int]] = mapped_column(Integer)
    alim1_litre: Mapped[Optional[float]] = mapped_column(Float)

    alim2_tarih: Mapped[Optional[date]] = mapped_column(Date)
    alim2_km: Mapped[Optional[int]] = mapped_column(Integer)

    ara_mesafe: Mapped[Optional[int]] = mapped_column(Integer)
    toplam_yakit: Mapped[Optional[float]] = mapped_column(Float)
    ort_tuketim: Mapped[Optional[float]] = mapped_column(Float)
    sefer_sayisi: Mapped[int] = mapped_column(Integer, default=0)
    durum: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationships
    arac: Mapped["Arac"] = relationship(back_populates="yakit_periyotlari")


class YakitFormul(Base):
    __tablename__ = "yakit_formul"

    id: Mapped[int] = mapped_column(primary_key=True)
    arac_id: Mapped[int] = mapped_column(
        ForeignKey("araclar.id", ondelete="RESTRICT"), unique=True
    )
    katsayilar: Mapped[dict] = mapped_column(JSON)  # JSON type for katsayilar
    r2_score: Mapped[Optional[float]] = mapped_column(Float)
    sample_count: Mapped[Optional[int]] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    arac: Mapped["Arac"] = relationship(back_populates="formul")


class Rol(Base):
    __tablename__ = "roller"

    id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    yetkiler: Mapped[dict] = mapped_column(
        JSON, server_default=text("'{}'"), nullable=False
    )
    olusturma: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ad_soyad: Mapped[str] = mapped_column(String(100), nullable=False)
    sifre_hash: Mapped[str] = mapped_column(Text, nullable=False)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roller.id"), nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Oturum ve Güvenlik
    son_giris: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    son_giris_ip: Mapped[Optional[str]] = mapped_column(String(45))
    basarisiz_giris_sayisi: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    kilitli_kadar: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Şifre yönetimi
    sifre_degisim_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sifre_sifir_token: Mapped[Optional[str]] = mapped_column(Text)
    sifre_sifir_son: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Existing linkage
    sofor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("soforler.id", ondelete="SET NULL"), index=True
    )

    # Zaman damgaları
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    olusturan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("kullanicilar.id"))

    # Relationships
    rol: Mapped["Rol"] = relationship()
    oturumlari: Mapped[List["KullaniciOturumu"]] = relationship(
        back_populates="kullanici", cascade="all, delete-orphan"
    )
    bildirimler: Mapped[List["BildirimGecmisi"]] = relationship(
        back_populates="kullanici", cascade="all, delete-orphan"
    )
    ayarlar: Mapped[List["KullaniciAyari"]] = relationship(
        back_populates="kullanici", cascade="all, delete-orphan"
    )


class KullaniciOturumu(Base):
    __tablename__ = "kullanici_oturumlari"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    kullanici_id: Mapped[int] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False
    )
    access_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(Text)
    ip_adresi: Mapped[str] = mapped_column(String(45), nullable=False)
    tarayici: Mapped[Optional[str]] = mapped_column(Text)
    olusturma: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    son_aktivite: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    access_bitis: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    refresh_bitis: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    iptal_sebebi: Mapped[Optional[str]] = mapped_column(Text)

    kullanici: Mapped["Kullanici"] = relationship(back_populates="oturumlari")


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    kullanici_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="SET NULL")
    )
    kullanici_email: Mapped[Optional[str]] = mapped_column(String(255))
    aksiyon_tipi: Mapped[str] = mapped_column(String(100), nullable=False)
    hedef_tablo: Mapped[Optional[str]] = mapped_column(String(100))
    hedef_id: Mapped[Optional[str]] = mapped_column(Text)
    aciklama: Mapped[Optional[str]] = mapped_column(Text)
    eski_deger: Mapped[Optional[dict]] = mapped_column(JSON)
    yeni_deger: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_adresi: Mapped[Optional[str]] = mapped_column(String(45))
    tarayici: Mapped[Optional[str]] = mapped_column(Text)
    istek_id: Mapped[Optional[str]] = mapped_column(String(36))  # UUID as string
    basarili: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hata_mesaji: Mapped[Optional[str]] = mapped_column(Text)
    sure_ms: Mapped[Optional[int]] = mapped_column(Integer)
    zaman: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Anomaly(Base):
    """Anomali kayıtları - AI Tespit sonuçlarını saklar"""

    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True)
    tarih: Mapped[date] = mapped_column(Date, index=True)
    tip: Mapped[str] = mapped_column(String(50), index=True)  # tuketim, maliyet, sefer
    kaynak_tip: Mapped[str] = mapped_column(String(50))  # arac, sofor, sefer, yakit
    kaynak_id: Mapped[int] = mapped_column(Integer, index=True)
    deger: Mapped[float] = mapped_column(Float)
    beklenen_deger: Mapped[float] = mapped_column(Float)
    sapma_yuzde: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high, critical
    aciklama: Mapped[str] = mapped_column(Text)
    rca_summary: Mapped[Optional[str]] = mapped_column(Text)
    suggested_action: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )


class RoutePath(Base):
    """Rota Geometrisi Önbelleği - API Kota Tasarrufu için"""

    __tablename__ = "route_paths"
    __table_args__ = (
        UniqueConstraint(
            "origin_lat", "origin_lon", "dest_lat", "dest_lon", name="uq_route_coords"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    origin_lat: Mapped[float] = mapped_column(Float, index=True)
    origin_lon: Mapped[float] = mapped_column(Float, index=True)
    dest_lat: Mapped[float] = mapped_column(Float, index=True)
    dest_lon: Mapped[float] = mapped_column(Float, index=True)

    distance_km: Mapped[float] = mapped_column(Float)
    duration_min: Mapped[float] = mapped_column(Float)
    ascent_m: Mapped[float] = mapped_column(Float, default=0.0)
    descent_m: Mapped[float] = mapped_column(Float, default=0.0)
    flat_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    geometry: Mapped[dict] = mapped_column(JSON)  # GeoJSON formatında rota çizgisi
    fuel_estimate_cache: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # Tahmin sonucu önbelleği

    last_fetched: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EgitimKuyrugu(Base):
    """ML Model eğitim görev kuyruğu"""

    __tablename__ = "egitim_kuyrugu"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    arac_id: Mapped[int] = mapped_column(
        ForeignKey("araclar.id", ondelete="CASCADE"), index=True
    )
    hedef_versiyon: Mapped[int] = mapped_column(Integer, nullable=False)

    # Durumlar: WAITING, RUNNING, COMPLETED, FAILED, CANCELED
    durum: Mapped[str] = mapped_column(
        String(20), default="WAITING", index=True, nullable=False
    )
    ilerleme: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # 0.0 - 100.0

    # Hata yonetimi
    hata_detay: Mapped[Optional[str]] = mapped_column(Text)
    yeniden_deneme_sayisi: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Zamanlayıcılar
    baslangic_zaman: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    bitis_zaman: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    olusturma: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    guncelleme: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # İsteğe bağlı, kimin veya sistemin tetiklediği
    tetikleyen_kullanici_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="SET NULL")
    )

    # Relationships
    arac: Mapped["Arac"] = relationship()
    tetikleyen: Mapped[Optional["Kullanici"]] = relationship()


class ModelVersiyon(Base):
    """Model versiyonları - Versiyonlama ve Rollback için"""

    __tablename__ = "model_versiyonlar"

    id: Mapped[int] = mapped_column(primary_key=True)
    arac_id: Mapped[int] = mapped_column(
        ForeignKey("araclar.id", ondelete="CASCADE"), index=True
    )
    versiyon: Mapped[int] = mapped_column(Integer, nullable=False)
    egitim_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=get_utc_now,
    )
    veri_sayisi: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Performans metrikleri
    r2_skoru: Mapped[Optional[float]] = mapped_column(Float)
    mae: Mapped[Optional[float]] = mapped_column(Float)
    mape: Mapped[Optional[float]] = mapped_column(Float)
    rmse: Mapped[Optional[float]] = mapped_column(Float)

    # Model detayları
    model_dosya_yolu: Mapped[Optional[str]] = mapped_column(Text)
    model_boyut_kb: Mapped[Optional[int]] = mapped_column(Integer)
    egitim_suresi_sn: Mapped[Optional[float]] = mapped_column(Float)
    kullanilan_ozellikler: Mapped[Optional[dict]] = mapped_column(JSON)

    # Model ağırlıkları (ensemble)
    xgboost_agirligi: Mapped[Optional[float]] = mapped_column(Float)
    lightgbm_agirligi: Mapped[Optional[float]] = mapped_column(Float)
    rf_agirligi: Mapped[Optional[float]] = mapped_column(Float)
    gb_agirligi: Mapped[Optional[float]] = mapped_column(Float)
    fizik_agirligi: Mapped[Optional[float]] = mapped_column(Float)

    # Durum
    aktif: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fizik_only_mod: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fizik_only_sebebi: Mapped[Optional[str]] = mapped_column(Text)

    # Meta
    notlar: Mapped[Optional[str]] = mapped_column(Text)
    egiten_kullanici_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kullanicilar.id")
    )
    tetikleyici: Mapped[str] = mapped_column(String(50), default="otomatik")

    # Relationships
    arac: Mapped["Arac"] = relationship()
    egiten_kullanici: Mapped[Optional["Kullanici"]] = relationship()

    __table_args__ = (
        UniqueConstraint("arac_id", "versiyon", name="uq_arac_versiyon"),
        Index("idx_model_arac_versiyon", "arac_id", text("versiyon DESC")),
    )


class VehicleEventLog(Base, AsyncAttrs):
    __tablename__ = "vehicle_event_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    arac_id: Mapped[int] = mapped_column(
        ForeignKey("araclar.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    old_status: Mapped[Optional[str]] = mapped_column(String(50))
    new_status: Mapped[Optional[str]] = mapped_column(String(50))
    triggered_by: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    details: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=get_utc_now,
    )

    arac: Mapped["Arac"] = relationship(back_populates="event_logs")


class SistemKonfig(Base):
    __tablename__ = "sistem_konfig"

    anahtar: Mapped[str] = mapped_column(String(100), primary_key=True)
    deger: Mapped[dict] = mapped_column(JSON, nullable=False)
    tip: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # string, number, boolean, json
    birim: Mapped[Optional[str]] = mapped_column(String(20))
    min_deger: Mapped[Optional[float]] = mapped_column(Float)
    max_deger: Mapped[Optional[float]] = mapped_column(Float)
    grup: Mapped[str] = mapped_column(String(50), nullable=False)
    aciklama: Mapped[Optional[str]] = mapped_column(Text)
    yeniden_baslat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    son_guncelleme: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    guncelleyen_id: Mapped[Optional[int]] = mapped_column(ForeignKey("kullanicilar.id"))


class KonfigGecmis(Base):
    __tablename__ = "konfig_gecmis"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    anahtar: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    eski_deger: Mapped[dict] = mapped_column(JSON, nullable=False)
    yeni_deger: Mapped[dict] = mapped_column(JSON, nullable=False)
    degisiklik_sebebi: Mapped[Optional[str]] = mapped_column(Text)
    guncelleyen_id: Mapped[Optional[int]] = mapped_column(ForeignKey("kullanicilar.id"))
    zaman: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IceriAktarimGecmisi(Base):
    """
    Import History for bulk data ingestion tracking and rollback capability.
    """

    __tablename__ = "iceri_aktarim_gecmisi"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    dosya_adi: Mapped[str] = mapped_column(String(255), nullable=False)
    aktarim_tipi: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g. "arac", "surucu"

    # Durumlar: PENDING, VALIDATING, PROCESSING, COMPLETED, FAILED, ROLLED_BACK
    durum: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING", index=True
    )

    toplam_kayit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    basarili_kayit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hatali_kayit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    islem_haritasi: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # Storing row-to-DB ID mappings for rollback
    hatalar: Mapped[Optional[dict]] = mapped_column(JSON)  # Detailed errors per row

    yukleyen_id: Mapped[Optional[int]] = mapped_column(ForeignKey("kullanicilar.id"))

    baslama_zamani: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    bitis_zamani: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Optional constraint check tracking for safe deletions
    rollback_baglantilari: Mapped[Optional[dict]] = mapped_column(JSON)


class GuzergahKalibrasyon(Base):
    __tablename__ = "guzergah_kalibrasyonlari"

    id: Mapped[int] = mapped_column(primary_key=True)
    lokasyon_id: Mapped[int] = mapped_column(
        ForeignKey("lokasyonlar.id", ondelete="CASCADE"), index=True
    )

    # Calibration details
    # hedef_path: Mapped[Optional[Any]] = mapped_column(Geometry("LINESTRING", srid=4326))
    buffer_meters: Mapped[float] = mapped_column(
        Float, default=250.0
    )  # Acceptable deviation

    # Accuracy stats
    match_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_deviation_dist: Mapped[float] = mapped_column(Float, default=0.0)

    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )

    # Relationships
    lokasyon: Mapped["Lokasyon"] = relationship(back_populates="kalibrasyonlar")


class AracBakim(Base):
    __tablename__ = "arac_bakimlari"

    # Modifying maintenance logic to support either an Arac or a Dorse
    id: Mapped[int] = mapped_column(primary_key=True)
    arac_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("araclar.id", ondelete="CASCADE"), index=True
    )
    dorse_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("dorseler.id", ondelete="CASCADE"), index=True
    )
    bakim_tipi: Mapped[BakimTipi] = mapped_column(
        String(20), default=BakimTipi.PERIYODIK
    )
    km_bilgisi: Mapped[int] = mapped_column(Integer)
    bakim_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    maliyet: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    detaylar: Mapped[Optional[str]] = mapped_column(Text)
    tamamlandi: Mapped[bool] = mapped_column(Boolean, default=False)

    guncelleme_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    arac: Mapped[Optional["Arac"]] = relationship(back_populates="bakimlar")
    dorse: Mapped[Optional["Dorse"]] = relationship(back_populates="bakimlar")


class BildirimKurali(Base):
    __tablename__ = "bildirim_kurallari"

    id: Mapped[int] = mapped_column(primary_key=True)
    olay_tipi: Mapped[str] = mapped_column(String(50), index=True)
    kanallar: Mapped[List[str]] = mapped_column(JSON)
    alici_rol_id: Mapped[int] = mapped_column(Integer)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)


class BildirimDurumu(str, enum.Enum):
    SENT = "SENT"
    FAILED = "FAILED"
    READ = "READ"


class BildirimGecmisi(Base):
    __tablename__ = "bildirim_gecmisi"

    id: Mapped[int] = mapped_column(primary_key=True)
    kullanici_id: Mapped[int] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="CASCADE"), index=True
    )
    baslik: Mapped[str] = mapped_column(String(200))
    icerik: Mapped[str] = mapped_column(Text)
    olay_tipi: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    kanal: Mapped[str] = mapped_column(String(20))
    durum: Mapped[BildirimDurumu] = mapped_column(
        String(20), default=BildirimDurumu.SENT
    )
    okundu_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )

    # Relationships
    kullanici: Mapped["Kullanici"] = relationship(back_populates="bildirimler")


class KullaniciAyari(Base):
    """
    User-specific preferences for different modules and settings types.
    e.g. Saved filters for 'seferler' module or column visibility for 'araclar' table.
    """

    __tablename__ = "kullanici_ayarlari"

    id: Mapped[int] = mapped_column(primary_key=True)
    kullanici_id: Mapped[int] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="CASCADE"), index=True
    )
    modul: Mapped[str] = mapped_column(
        String(50), index=True
    )  # 'seferler', 'araclar', etc.
    ayar_tipi: Mapped[str] = mapped_column(String(50), index=True)  # 'filtre', 'sutun'
    deger: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    ad: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # Friendly name for saved filters

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=get_utc_now
    )

    # Relationships
    kullanici: Mapped["Kullanici"] = relationship(back_populates="ayarlar")


class PredictionResult(Base):
    """
    Kuyruklu tahmin sonuçlarının kalıcı kaydı (task_id bazlı).
    """

    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kullanicilar.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=get_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=get_utc_now
    )
