"""
Pydantic Schemas için kapsamlı güvenlik test suite.

Test kategorileri:
- Sensitive Data Protection
- String Validation (length, XSS, null byte)
- Numeric Validation
- Date Validation
- Injection Protection
- Edge Cases
"""

import pytest
from pydantic import ValidationError
from datetime import date, datetime
from decimal import Decimal

# Import schemas
from app.schemas.arac import AracCreate
from app.schemas.prediction import PredictionRequest, TrainingResponse
from app.schemas.sefer import SeferCreate
from app.schemas.sofor import SoforCreate, SoforUpdate
from app.schemas.user import KullaniciCreate, KullaniciRead
from app.schemas.yakit import YakitCreate
from app.schemas.validators import (
    sanitize_string,
    validate_safe_string,
    check_xss,
    mask_phone,
    validate_dict_size,
)


# ============================================================================
# SENSITIVE DATA PROTECTION TESTS
# ============================================================================


class TestSensitiveDataProtection:
    """Sensitive data koruması testleri."""

    def test_password_not_in_response(self):
        """Password response model'de olmamalı."""
        fields = KullaniciRead.model_fields.keys()
        assert "password" not in fields
        assert "password_hash" not in fields
        assert "sifre" not in fields
        assert "sifre_hash" not in fields

    def test_token_not_exposed(self):
        """Token/secret expose edilmemeli."""
        fields = KullaniciRead.model_fields.keys()
        assert "token" not in fields
        assert "access_token" not in fields
        assert "secret" not in fields

    def test_phone_masked_in_response(self):
        """Telefon response'da maskelenmeli."""
        # mask_phone fonksiyonu test
        assert mask_phone("0532 123 45 67") == "0532 *** ** 67"
        assert mask_phone("05321234567") == "0532 *** ** 67"
        assert mask_phone(None) is None
        assert mask_phone("") == ""


# ============================================================================
# STRING VALIDATION TESTS
# ============================================================================


class TestStringValidation:
    """String field validation testleri."""

    def test_max_length_enforced_arac_plaka(self):
        """Arac plaka max length zorlanmalı."""
        with pytest.raises(ValidationError) as excinfo:
            AracCreate(plaka="A" * 100, marka="Test")
        assert "String should have at most" in str(
            excinfo.value
        ) or "most 20 characters" in str(excinfo.value)

    def test_max_length_enforced_arac_marka(self):
        """Arac marka max length zorlanmalı."""
        with pytest.raises(ValidationError):
            AracCreate(plaka="34ABC123", marka="A" * 51)

    def test_min_length_enforced(self):
        """Minimum uzunluk zorlanmalı."""
        with pytest.raises(ValidationError):
            AracCreate(plaka="34A", marka="Test")  # plaka min 5 karakter

    def test_empty_string_rejected_required_field(self):
        """Boş string zorunlu field'da reddedilmeli."""
        with pytest.raises(ValidationError):
            AracCreate(plaka="", marka="Test")

    def test_whitespace_only_rejected(self):
        """Sadece boşluk karakteri reddedilmeli."""
        with pytest.raises(ValidationError):
            AracCreate(plaka="     ", marka="Test")

    def test_turkish_characters_accepted(self):
        """Türkçe karakterler kabul edilmeli."""
        sofor = SoforCreate(ad_soyad="İsmail Şoför Öğretici")
        assert "İsmail" in sofor.ad_soyad
        assert "Şoför" in sofor.ad_soyad
        assert "Öğretici" in sofor.ad_soyad

    def test_whitespace_stripping(self):
        """Whitespace strip edilmeli."""
        arac = AracCreate(plaka="  34ABC123  ", marka="  Ford  ")
        assert arac.plaka == "34ABC123"
        assert arac.marka == "Ford"


# ============================================================================
# XSS/INJECTION PROTECTION TESTS
# ============================================================================


class TestInjectionProtection:
    """Injection koruması testleri."""

    def test_xss_script_tag_rejected(self):
        """Script tag reddedilmeli."""
        with pytest.raises(ValueError) as excinfo:
            check_xss("<script>alert('xss')</script>")
        assert "XSS" in str(excinfo.value)

    def test_xss_javascript_protocol_rejected(self):
        """javascript: protocol reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss("javascript:alert('xss')")

    def test_xss_event_handler_rejected(self):
        """Event handler (onclick vb.) reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss('<img onerror="alert(1)">')

    def test_xss_iframe_rejected(self):
        """iframe reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss('<iframe src="evil.com"></iframe>')

    def test_null_byte_sanitized(self):
        """Null byte temizlenmeli."""
        result = sanitize_string("test\x00injection")
        assert "\x00" not in result
        assert result == "testinjection"

    def test_sefer_location_xss_protection(self):
        """Sefer çıkış/varış yeri XSS koruması."""
        with pytest.raises(ValidationError):
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="<script>alert('xss')</script>",
                varis_yeri="Normal Yer",
                mesafe_km=100,
            )

    def test_arac_notlar_xss_protection(self):
        """Araç notları XSS koruması."""
        with pytest.raises(ValidationError):
            AracCreate(
                plaka="34ABC123", marka="Ford", notlar="<script>alert('xss')</script>"
            )

    def test_yakit_istasyon_xss_protection(self):
        """Yakıt istasyon XSS koruması."""
        with pytest.raises(ValidationError):
            YakitCreate(
                tarih=date.today(),
                arac_id=1,
                istasyon="<script>alert('xss')</script>",
                fiyat_tl=Decimal("45.50"),
                litre=Decimal("100"),
                toplam_tutar=Decimal("4550"),
                km_sayac=50000,
            )

    def test_sql_injection_pattern_rejected(self):
        """SQL injection pattern'leri reddedilmeli."""
        with pytest.raises(ValueError):
            validate_safe_string("'; DROP TABLE users; --")

    def test_safe_string_passes_normal_input(self):
        """Normal input geçmeli."""
        result = validate_safe_string("Normal metin 123")
        assert result == "Normal metin 123"


# ============================================================================
# NUMERIC VALIDATION TESTS
# ============================================================================


class TestNumericValidation:
    """Numeric field validation testleri."""

    def test_negative_not_allowed_yakit_litre(self):
        """Negatif litre reddedilmeli."""
        with pytest.raises(ValidationError):
            YakitCreate(
                tarih=date.today(),
                arac_id=1,
                fiyat_tl=Decimal("45.50"),
                litre=Decimal("-100"),
                toplam_tutar=Decimal("4550"),
                km_sayac=50000,
            )

    def test_negative_not_allowed_sefer_mesafe(self):
        """Negatif mesafe reddedilmeli."""
        with pytest.raises(ValidationError):
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=-100,
            )

    def test_zero_not_allowed_where_gt_zero(self):
        """Sıfır gt=0 olan yerde reddedilmeli."""
        with pytest.raises(ValidationError):
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=0,  # gt=0 yani > 0 olmalı
            )

    def test_zero_allowed_where_ge_zero(self):
        """Sıfır ge=0 olan yerde kabul edilmeli."""
        sefer = SeferCreate(
            tarih=date.today(),
            arac_id=1,
            sofor_id=1,
            cikis_yeri="A",
            varis_yeri="B",
            mesafe_km=1,
            net_kg=0,  # ge=0 yani >= 0 olmalı
        )
        assert sefer.net_kg == 0

    def test_decimal_precision_yakit(self):
        """Decimal precision kontrolü."""
        yakit = YakitCreate(
            tarih=date.today(),
            arac_id=1,
            fiyat_tl=Decimal("45.99"),
            litre=Decimal("100.50"),
            toplam_tutar=Decimal("4622.00"),
            km_sayac=50000,
        )
        assert yakit.fiyat_tl == Decimal("45.99")


# ============================================================================
# DATE VALIDATION TESTS
# ============================================================================


class TestDateValidation:
    """Date/datetime validation testleri."""

    def test_future_year_limit_arac(self):
        """Araç yılı gelecekte çok uzak olamaz."""
        future_year = datetime.now().year + 5
        with pytest.raises(ValidationError) as excinfo:
            AracCreate(plaka="34ABC123", marka="Test", yil=future_year)
        assert "değerinden büyük olamaz" in str(excinfo.value)

    def test_current_year_allowed(self):
        """Şu anki yıl kabul edilmeli."""
        current_year = datetime.now().year
        arac = AracCreate(plaka="34ABC123", marka="Test", yil=current_year)
        assert arac.yil == current_year

    def test_next_year_allowed(self):
        """Gelecek yıl kabul edilmeli (fabrika üretimi)."""
        next_year = datetime.now().year + 1
        arac = AracCreate(plaka="34ABC123", marka="Test", yil=next_year)
        assert arac.yil == next_year


# ============================================================================
# PASSWORD VALIDATION TESTS
# ============================================================================


class TestPasswordValidation:
    """Şifre validasyon testleri."""

    def test_password_min_length(self):
        """Şifre minimum 8 karakter olmalı."""
        with pytest.raises(ValidationError):
            KullaniciCreate(
                email="test@lojinext.com",
                ad_soyad="Test User",
                rol_id=1,
                sifre="Short1",  # 6 karakter, min 8 gerekli
            )

    def test_password_needs_uppercase(self):
        """Şifre büyük harf içermeli."""
        with pytest.raises(ValidationError) as excinfo:
            KullaniciCreate(
                email="test@lojinext.com",
                ad_soyad="Test User",
                rol_id=1,
                sifre="lowercase123",
            )
        assert "büyük harf" in str(excinfo.value)

    def test_password_needs_lowercase(self):
        """Şifre küçük harf içermeli."""
        with pytest.raises(ValidationError) as excinfo:
            KullaniciCreate(
                email="test@lojinext.com",
                ad_soyad="Test User",
                rol_id=1,
                sifre="UPPERCASE123",
            )
        assert "küçük harf" in str(excinfo.value)

    def test_password_needs_digit(self):
        """Şifre rakam içermeli."""
        with pytest.raises(ValidationError) as excinfo:
            KullaniciCreate(
                email="test@lojinext.com",
                ad_soyad="Test User",
                rol_id=1,
                sifre="NoDigitsHere",
            )
        assert "rakam" in str(excinfo.value)

    def test_valid_password_accepted(self):
        """Geçerli şifre kabul edilmeli."""
        user = KullaniciCreate(
            email="test@lojinext.com",
            ad_soyad="Test User",
            rol_id=1,
            sifre="ValidPass123",
        )
        assert user.sifre == "ValidPass123"


# ============================================================================
# EMAIL VALIDATION TESTS
# ============================================================================


class TestEmailValidation:
    """Email validasyon testleri."""

    def test_email_format_valid(self):
        """Geçerli email formatları."""
        valid_emails = [
            "user@example.com",
            "first.last@domain.com",
            "user123@sub.domain.org",
        ]
        for email in valid_emails:
            user = KullaniciCreate(
                email=email, ad_soyad="Test User", rol_id=1, sifre="ValidPass123"
            )
            assert user.email == email

    def test_email_format_invalid(self):
        """Geçersiz email formatları reddedilmeli."""
        invalid_emails = [
            "user",
            "user@",
            "@domain.com",
            "user@domain..com",
            "user name@domain.com",
        ]
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                KullaniciCreate(
                    email=email, ad_soyad="Test User", rol_id=1, sifre="ValidPass123"
                )


# ============================================================================
# DICT SIZE VALIDATION TESTS (DoS Protection)
# ============================================================================


class TestDictSizeValidation:
    """Dict boyut kontrolü testleri (DoS koruması)."""

    def test_metrics_dict_size_limit(self):
        """Metrics dict boyutu sınırlı olmalı."""
        large_dict = {f"key_{i}": i for i in range(100)}
        result = validate_dict_size(large_dict, max_keys=100)
        assert result == large_dict

        # 101 key ile hata vermeli
        too_large_dict = {f"key_{i}": i for i in range(101)}
        with pytest.raises(ValueError):
            validate_dict_size(too_large_dict, max_keys=100)

    def test_training_response_metrics_limit(self):
        """TrainingResponse metrics limiti."""
        # 50 key ile OK
        response = TrainingResponse(
            status="success",
            model_type="xgboost",
            r2_score=0.95,
            sample_count=1000,
            metrics={f"metric_{i}": i for i in range(50)},
        )
        assert len(response.metrics) == 50


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Edge case testleri."""

    def test_unicode_emoji(self):
        """Unicode emoji handling."""
        # Emoji içeren isim - title() ile sorun olabilir
        result = sanitize_string("Test 🚛 Driver")
        assert "🚛" in result

    def test_control_characters_removed(self):
        """Control karakterleri temizlenmeli."""
        result = sanitize_string("test\x07bell\x08backspace")
        assert "\x07" not in result
        assert "\x08" not in result

    def test_rtl_characters(self):
        """RTL karakterler (Arapça, İbranice) handling."""
        result = sanitize_string("مرحبا")  # Arapça "Merhaba"
        assert result == "مرحبا"

    def test_empty_list_handling(self):
        """Boş liste handling."""
        # TrainingResponse metrics boş dict olabilir
        response = TrainingResponse(
            status="success",
            model_type="linear",
            r2_score=0.9,
            sample_count=100,
            metrics={},
        )
        assert response.metrics == {}

    def test_optional_field_missing(self):
        """Optional field eksik olduğunda default kullanılmalı."""
        arac = AracCreate(plaka="34ABC123", marka="Ford")
        assert arac.yil is None
        assert arac.tank_kapasitesi == 600  # default
        assert arac.hedef_tuketim == 32.0  # default
        assert arac.aktif is True  # default

    def test_optional_field_null(self):
        """Optional field None olarak verilebilmeli."""
        arac = AracCreate(plaka="34ABC123", marka="Ford", model=None)
        assert arac.model is None


# ============================================================================
# REGEX PATTERN TESTS
# ============================================================================


class TestRegexPatterns:
    """Regex pattern testleri."""

    def test_plaka_format_valid(self):
        """Geçerli plaka formatları."""
        valid_plakas = [
            "34ABC123",
            "34 ABC 123",
            "06A1234",
            "01ABC12",
        ]
        for plaka in valid_plakas:
            arac = AracCreate(plaka=plaka, marka="Test")
            assert arac.plaka.replace(" ", "") in plaka.replace(" ", "")

    def test_plaka_format_invalid(self):
        """Geçersiz plaka formatları reddedilmeli."""
        invalid_plakas = [
            "INVALID",
            "123ABC",  # Yanlış sıra
            "34 OR 1=1",  # SQL injection
            "34<script>",  # XSS
        ]
        for plaka in invalid_plakas:
            with pytest.raises(ValidationError):
                AracCreate(plaka=plaka, marka="Test")

    def test_telefon_format_valid(self):
        """Geçerli telefon formatları."""
        valid_phones = [
            "0532 123 45 67",
            "0 532 123 45 67",
            "5321234567",
        ]
        for phone in valid_phones:
            sofor = SoforCreate(ad_soyad="Test User", telefon=phone)
            assert sofor.telefon is not None

    def test_telefon_format_invalid(self):
        """Geçersiz telefon formatları reddedilmeli."""
        with pytest.raises(ValidationError):
            SoforCreate(ad_soyad="Test User", telefon="invalid-phone")

    def test_saat_format_valid(self):
        """Geçerli saat formatları."""
        valid_times = ["08:30", "23:59", "0:00", "12:00"]
        for time in valid_times:
            sefer = SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=100,
                saat=time,
            )
            assert sefer.saat == time

    def test_saat_format_invalid(self):
        """Geçersiz saat formatları reddedilmeli."""
        with pytest.raises(ValidationError):
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=100,
                saat="25:00",  # Geçersiz saat
            )


# ============================================================================
# LITERAL/ENUM TESTS
# ============================================================================


class TestLiteralEnums:
    """Literal enum validation testleri."""

    def test_sefer_durum_valid(self):
        """Geçerli sefer durumu."""
        for durum in ["Tamam", "Devam Ediyor", "İptal"]:
            sefer = SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=100,
                durum=durum,
            )
            assert sefer.durum == durum

    def test_sefer_durum_invalid(self):
        """Geçersiz sefer durumu reddedilmeli."""
        with pytest.raises(ValidationError):
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=100,
                durum="GeçersizDurum",
            )

    def test_yakit_durum_valid(self):
        """Geçerli yakıt durumu."""
        for durum in ["Bekliyor", "Onaylandı", "Reddedildi"]:
            yakit = YakitCreate(
                tarih=date.today(),
                arac_id=1,
                fiyat_tl=Decimal("45.50"),
                litre=Decimal("100"),
                toplam_tutar=Decimal("4550"),
                km_sayac=50000,
                durum=durum,
            )
            assert yakit.durum == durum

    def test_user_rol_valid(self):
        """Geçerli kullanıcı rolü."""
        # rol_id expects an integer FK
        for rol_id in [1, 2, 3]:
            user = KullaniciCreate(
                email=f"user{rol_id}@lojinext.com",
                ad_soyad=f"Test User {rol_id}",
                sifre="ValidPass123",
                rol_id=rol_id,
            )
            assert user.rol_id == rol_id

    def test_user_rol_invalid(self):
        """Geçersiz kullanıcı rolü reddedilmeli."""
        # rol_id must be provided
        with pytest.raises(ValidationError):
            KullaniciCreate(
                email="testuser@lojinext.com",
                ad_soyad="Test User",
                sifre="ValidPass123",
                # missing rol_id
            )


# ============================================================================
# MAX LIMIT TESTS (Overflow/DoS Protection)
# ============================================================================


class TestMaxLimits:
    """Maksimum limit testleri (overflow koruması)."""

    def test_tank_kapasitesi_max_limit(self):
        """Tank kapasitesi max 5000 litre."""
        with pytest.raises(ValidationError):
            AracCreate(plaka="34ABC123", marka="Test", tank_kapasitesi=10000)

    def test_hedef_tuketim_max_limit(self):
        """Hedef tüketim max 100 lt/100km."""
        with pytest.raises(ValidationError):
            AracCreate(plaka="34ABC123", marka="Test", hedef_tuketim=150)

    def test_mesafe_km_max_limit(self):
        """Mesafe max 10000 km."""
        with pytest.raises(ValidationError):
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=50000,
            )

    def test_km_sayac_max_limit(self):
        """KM sayaç max 9999999."""
        with pytest.raises(ValidationError):
            YakitCreate(
                tarih=date.today(),
                arac_id=1,
                fiyat_tl=Decimal("45.50"),
                litre=Decimal("100"),
                toplam_tutar=Decimal("4550"),
                km_sayac=99999999,
            )

    def test_prediction_mesafe_max_limit(self):
        """Prediction mesafe max 100000 km."""
        with pytest.raises(ValidationError):
            PredictionRequest(arac_id=1, mesafe_km=500000)


# ============================================================================
# KM RANGE VALIDATION TESTS
# ============================================================================


class TestKmRangeValidation:
    """Başlangıç/bitiş km mantıksal kontrol testleri."""

    def test_bitis_km_greater_than_baslangic(self):
        """Bitiş km başlangıçtan büyük olmalı."""
        with pytest.raises(ValidationError) as excinfo:
            SeferCreate(
                tarih=date.today(),
                arac_id=1,
                sofor_id=1,
                cikis_yeri="A",
                varis_yeri="B",
                mesafe_km=100,
                baslangic_km=50000,
                bitis_km=40000,  # Hata! 40000 < 50000
            )
        assert "büyük olmalı" in str(excinfo.value)

    def test_valid_km_range(self):
        """Geçerli km aralığı kabul edilmeli."""
        sefer = SeferCreate(
            tarih=date.today(),
            arac_id=1,
            sofor_id=1,
            cikis_yeri="A",
            varis_yeri="B",
            mesafe_km=100,
            baslangic_km=50000,
            bitis_km=50100,
        )
        assert sefer.bitis_km > sefer.baslangic_km


# ============================================================================
# ADDITIONAL XSS PATTERN TESTS
# ============================================================================


class TestAdditionalXssPatterns:
    """Yeni eklenen XSS pattern testleri."""

    def test_style_tag_rejected(self):
        """Style tag reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss("<style>body{display:none}</style>")

    def test_svg_tag_rejected(self):
        """SVG tag reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss('<svg onload="alert(1)">')

    def test_link_tag_rejected(self):
        """Link tag reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss('<link href="evil.css">')

    def test_meta_tag_rejected(self):
        """Meta tag reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss('<meta http-equiv="refresh">')

    def test_expression_rejected(self):
        """CSS expression reddedilmeli."""
        with pytest.raises(ValueError):
            check_xss("expression(alert(1))")

    def test_marka_xss_protection(self):
        """Marka alanı XSS koruması."""
        with pytest.raises(ValidationError):
            AracCreate(plaka="34ABC123", marka="<script>alert(1)</script>")


# ============================================================================
# SCORE VALIDATION TESTS
# ============================================================================


class TestScoreValidation:
    """Şoför score validasyon testleri."""

    def test_score_valid_range(self):
        """Geçerli score değerleri."""
        for score in [0.1, 1.0, 1.5, 2.0]:
            sofor = SoforCreate(ad_soyad="Test User", score=score)
            assert sofor.score == score

    def test_score_out_of_range_update(self):
        """SoforUpdate'de geçersiz score reddedilmeli."""
        with pytest.raises(ValidationError):
            SoforUpdate(score=2.1)  # Max 2.0
