"""
TIR Yakıt Takip Sistemi - Veri Doğrulama Servisi
Veri tutarlılığını ve bütünlüğünü kontrol eden servis.
"""

from typing import Any, Dict, List

from app.database.unit_of_work import UnitOfWork
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class VerifierService:
    """
    Sistem genelinde veri tutarlılığını kontrol eden servis.
    Özellikle Sefer-Yakıt eşleşmeleri ve kümülatif hesaplamalar için kullanılır.
    """

    async def verify_trip_integrity(self) -> Dict[str, Any]:
        """
        Tüm seferlerin veri bütünlüğünü kontrol eder.
        """
        results = {
            "total_trips": 0,
            "suspicious_count": 0,
            "anomalies": [],
        }

        async with UnitOfWork() as uow:
            # 1. Temel İstatistikler
            total = await uow.sefer_repo.count_all()
            results["total_trips"] = total

            # 2. Şüpheli Seferler (Repository üzerinden)
            suspicious_trips = await uow.sefer_repo.get_suspicious_trips(limit=50)

            results["suspicious_count"] = len(suspicious_trips)

            if suspicious_trips:
                results["anomalies"].append(
                    {
                        "type": "COMPLETED_NO_FUEL",
                        "count": len(suspicious_trips),
                        "details": [
                            {
                                "id": t["id"],
                                "plaka": t["plaka"],
                                "date": str(t["tarih"]),
                            }
                            for t in suspicious_trips
                        ],
                    }
                )

        return results

    async def detect_unmatched_fuel(self) -> List[int]:
        """
        Herhangi bir sefere bağlanmamış yakıt kayıtlarını bulur.
        """
        unmatched_ids = []
        async with UnitOfWork() as uow:
            # Mantık: Yakıt tarihi ile o aracın sefer tarihleri örtüşüyor mu?
            # Gelecekte implemente edilecek.
            pass

        return unmatched_ids


def get_verifier_service() -> VerifierService:
    return VerifierService()
