from datetime import date, datetime
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Arac(Base):
    __tablename__ = "araclar"

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
        DateTime, server_default=func.now(), default=datetime.now
    )

    # Relationships
    yakit_alimlari: Mapped[List["YakitAlimi"]] = relationship(
        back_populates="arac", cascade="all, delete-orphan"
    )
    seferler: Mapped[List["Sefer"]] = relationship(back_populates="arac")
    yakit_periyotlari: Mapped[List["YakitPeriyodu"]] = relationship(
        back_populates="arac"
    )
    formul: Mapped[Optional["YakitFormul"]] = relationship(
        back_populates="arac", uselist=False
    )


class Sofor(Base):
    __tablename__ = "soforler"

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

    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    notlar: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), default=datetime.now
    )

    # Relationships
    seferler: Mapped[List["Sefer"]] = relationship(back_populates="sofor")


class Lokasyon(Base):
    __tablename__ = "lokasyonlar"
    __table_args__ = (
        UniqueConstraint("cikis_yeri", "varis_yeri", name="uq_cikis_varis"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cikis_yeri: Mapped[str] = mapped_column(String(100))
    varis_yeri: Mapped[str] = mapped_column(String(100))
    mesafe_km: Mapped[int] = mapped_column(Integer)
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
    tahmini_yakit_lt: Mapped[Optional[float]] = mapped_column(Float)
    last_api_call: Mapped[Optional[datetime]] = mapped_column(DateTime)

    aktif: Mapped[bool] = mapped_column(Boolean, default=True)  # Soft delete flag
    notlar: Mapped[Optional[str]] = mapped_column(Text)


class YakitAlimi(Base):
    __tablename__ = "yakit_alimlari"

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
        DateTime, server_default=func.now(), default=datetime.now
    )

    # Relationships
    arac: Mapped["Arac"] = relationship(back_populates="yakit_alimlari")

    last_fetched: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Guzergah(Base):
    """
    Güzergah (Route) Tanımı
    Standart sefer rotalarını tanımlar.
    """

    __tablename__ = "guzergahlar"

    id: Mapped[int] = mapped_column(primary_key=True)
    ad: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )  # Örn: "Ankara - İstanbul (Standart)"
    cikis_yeri: Mapped[str] = mapped_column(String(100))
    varis_yeri: Mapped[str] = mapped_column(String(100))
    mesafe_km: Mapped[int] = mapped_column(Integer)

    # Defaults
    varsayilan_arac_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("araclar.id", ondelete="SET NULL")
    )
    varsayilan_sofor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("soforler.id", ondelete="SET NULL")
    )

    notlar: Mapped[Optional[str]] = mapped_column(Text)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    varsayilan_arac: Mapped[Optional["Arac"]] = relationship()
    varsayilan_sofor: Mapped[Optional["Sofor"]] = relationship()
    seferler: Mapped[List["Sefer"]] = relationship(back_populates="guzergah")


class Sefer(Base):
    __tablename__ = "seferler"

    id: Mapped[int] = mapped_column(primary_key=True)
    tarih: Mapped[date] = mapped_column(Date, index=True)
    saat: Mapped[Optional[str]] = mapped_column(String(5))

    # Foreign Keys
    guzergah_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("guzergahlar.id", ondelete="SET NULL"), index=True
    )
    arac_id: Mapped[int] = mapped_column(
        ForeignKey("araclar.id", ondelete="RESTRICT"), index=True
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
    mesafe_km: Mapped[int] = mapped_column(Integer)
    baslangic_km: Mapped[Optional[int]] = mapped_column(Integer)
    bitis_km: Mapped[Optional[int]] = mapped_column(Integer)

    # Trip Status & Details
    bos_sefer: Mapped[bool] = mapped_column(Boolean, default=False)
    durum: Mapped[str] = mapped_column(String(20), default="Tamam")
    notlar: Mapped[Optional[str]] = mapped_column(String(255))

    # Fuel & API Data
    dagitilan_yakit: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    tahmini_tuketim: Mapped[Optional[float]] = mapped_column(
        Float
    )  # AI predicted consumption
    rota_detay: Mapped[Optional[dict]] = mapped_column(JSON)  # Route path and details
    tuketim: Mapped[Optional[float]] = mapped_column(Float)
    ascent_m: Mapped[Optional[float]] = mapped_column(Float)
    descent_m: Mapped[Optional[float]] = mapped_column(Float)

    # Meta
    # aktif: Mapped[bool] = mapped_column(Boolean, default=True)  # REMOVED - Hard Delete
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), default=datetime.now
    )

    # Relationships
    arac: Mapped["Arac"] = relationship(back_populates="seferler")
    sofor: Mapped["Sofor"] = relationship(back_populates="seferler")
    guzergah: Mapped[Optional["Guzergah"]] = relationship(back_populates="seferler")


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


class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id: Mapped[int] = mapped_column(primary_key=True)
    kullanici_adi: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    sifre_hash: Mapped[str] = mapped_column(String(255))
    ad_soyad: Mapped[Optional[str]] = mapped_column(String(100))
    rol: Mapped[str] = mapped_column(String(20), default="user")
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    son_giris: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Ayarlar(Base):
    __tablename__ = "ayarlar"

    anahtar: Mapped[str] = mapped_column(String(100), primary_key=True)
    deger: Mapped[Optional[str]] = mapped_column(Text)
    aciklama: Mapped[Optional[str]] = mapped_column(Text)


class Alert(Base):
    """Uyarı/Bildirim modeli - Alerts API için veritabanı tablosu"""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # fuel_anomaly, cost_anomaly, driver_alert, vehicle_alert, system
    severity: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, critical
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default="unread", index=True
    )  # unread, read, dismissed
    source_id: Mapped[Optional[int]] = mapped_column(Integer)  # İlgili kaydın ID'si
    source_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # arac, sofor, sefer, yakit
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


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

    geometry: Mapped[dict] = mapped_column(JSON)  # GeoJSON formatında rota çizgisi
    fuel_estimate_cache: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # Tahmin sonucu önbelleği

    last_fetched: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
