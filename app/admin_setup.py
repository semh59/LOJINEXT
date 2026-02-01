"""
TIR Yakıt Takip - Admin Kullanıcı Güncelleme
Bu script mevcut veritabanına 'skara' admin kullanıcısını ekler.

Kullanım: python admin_setup.py
"""

import os
import sys
from pathlib import Path

import bcrypt

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# .env dosyasını yükle
from dotenv import load_dotenv

load_dotenv()


def setup_skara_admin():
    """skara admin kullanıcısını oluştur veya güncelle"""

    from app.database.db_manager import get_db

    db = get_db()

    # Şifre .env'den al veya varsayılan kullan
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme123!")

    # Bcrypt hash oluştur
    sifre_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

    with db.get_connection() as conn:
        # skara kullanıcısı var mı kontrol et
        existing = conn.execute(
            "SELECT id FROM kullanicilar WHERE kullanici_adi = ?",
            ("skara",)
        ).fetchone()

        if existing:
            # Güncelle (şifreyi yenile)
            conn.execute("""
                UPDATE kullanicilar 
                SET sifre_hash = ?, rol = 'admin', aktif = 1
                WHERE kullanici_adi = ?
            """, (sifre_hash, "skara"))
            print("✅ 'skara' kullanıcısı güncellendi!")
        else:
            # Yeni ekle
            conn.execute("""
                INSERT INTO kullanicilar 
                (kullanici_adi, sifre_hash, ad_soyad, rol, aktif)
                VALUES (?, ?, ?, ?, ?)
            """, ("skara", sifre_hash, "Sistem Yöneticisi", "admin", 1))
            print("✅ 'skara' kullanıcısı oluşturuldu!")

    print("\n📋 Giriş Bilgileri:")
    print("   Kullanıcı Adı: skara")
    print("   Şifre: [.env dosyasında DEFAULT_ADMIN_PASSWORD değerini kullanın]")
    print("\n⚠️ Güvenlik için ilk girişte şifrenizi değiştirmeniz önerilir.")


if __name__ == "__main__":
    setup_skara_admin()
