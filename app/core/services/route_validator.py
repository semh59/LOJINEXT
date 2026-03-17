from typing import Dict


class RouteValidator:
    """
    Güzergah verisi doğrulama ve düzeltme servisi.
    Anormal verileri tespit eder ve makul sınırlara çeker.
    """

    # Maksimum eğim (Grade) limitleri
    MAX_HIGHWAY_GRADE = 0.06  # %6 (Standart otoyol max)
    MAX_TRUCK_ROUTE_GRADE = 0.08  # %8 (TIR güzergahı max)

    # Anomali eşiği (Türkiye otoyolları için kümülatif eğim limiti)
    # Tırmanış / Mesafe oranı
    SUSPICIOUS_GRADE_THRESHOLD = 0.010  # %1.0 (Büyük ölçekli gürültü filtresi)
    CORRECTION_GRADE_CAP = 0.015  # %1.5

    @staticmethod
    def validate_and_correct(route_data: Dict) -> Dict:
        """
        Rota verisini analiz et ve gerekirse düzelt.

        Args:
            route_data: {
                'distance_km': float,
                'ascent_m': float,
                'descent_m': float,
                ...
            }

        Returns:
            Düzeltilmiş route_data (kopya) orjinali bozmaz.
        """
        # Kopya al
        data = route_data.copy()

        dist_km = data.get("distance_km") or data.get("mesafe_km") or 0
        ascent = data.get("ascent_m") or 0
        descent = data.get("descent_m") or 0

        if dist_km <= 0:
            return data

        # 1. Eğim Kontrolü (Grade Check)
        is_corrected = False
        reasons = []

        # Ascent Check
        avg_incline = ascent / (dist_km * 1000)
        if avg_incline > RouteValidator.SUSPICIOUS_GRADE_THRESHOLD:
            # Otomatik düzeltme: %1.5
            ascent = round(dist_km * 1000 * RouteValidator.CORRECTION_GRADE_CAP, 1)
            is_corrected = True
            reasons.append(f"High Incline ({avg_incline:.1%})")

        # Descent Check
        avg_decline = descent / (dist_km * 1000)
        if avg_decline > RouteValidator.SUSPICIOUS_GRADE_THRESHOLD:
            # Otomatik düzeltme: %1.5
            descent = round(dist_km * 1000 * RouteValidator.CORRECTION_GRADE_CAP, 1)
            is_corrected = True
            reasons.append(f"High Decline ({avg_decline:.1%})")

        data["is_corrected"] = is_corrected
        if is_corrected:
            data["ascent_m"] = ascent
            data["descent_m"] = descent
            data["correction_reason"] = " | ".join(reasons)

        return data
