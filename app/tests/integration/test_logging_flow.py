import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import json
import logging
import uuid

from fastapi.testclient import TestClient

from app.infrastructure.logging.logger import LOG_DIR, get_audit_logger
from app.main import app

client = TestClient(app)


def test_request_logging_and_correlation_id():
    """
    Test: RequestLoggingMiddleware çalışıyor mu?
    Beklenti:
    1. X-Correlation-ID header'ı yanıtla dönmeli.
    2. Log dosyasına 'Incoming Request' ve 'Request Completed' düşmeli.
    """
    import time

    # Log handler'ları flush et
    for handler in logging.getLogger().handlers:
        handler.flush()

    # 1. İstek gönder
    response = client.get("/api/v1/health/")
    assert response.status_code == 200

    # 2. Header kontrolü
    assert "X-Correlation-ID" in response.headers
    correlation_id = response.headers["X-Correlation-ID"]
    assert len(correlation_id) > 0

    # Handler'ları tekrar flush et
    for handler in logging.getLogger().handlers:
        handler.flush()
    time.sleep(0.1)  # Disk yazımı için kısa bekleme

    # 3. Log dosyası kontrolü (tir_yakit.log)
    log_file = LOG_DIR / "tir_yakit.log"
    assert log_file.exists(), f"Log dosyası bulunamadı: {log_file}"

    # Log dosyasını oku ve correlation_id'yi ara
    found_request = False
    found_response = False

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                log_entry = json.loads(line)
                entry_corr_id = log_entry.get("correlation_id")
                if entry_corr_id == correlation_id:
                    msg = log_entry.get("message", "")
                    if "Incoming Request" in msg:
                        found_request = True
                    if "Request Completed" in msg or "Slow Request" in msg:
                        found_response = True
                        assert "latency_ms" in log_entry, "latency_ms alanı eksik"
            except json.JSONDecodeError:
                continue

    assert found_request, f"İstek logu bulunamadı (correlation_id: {correlation_id})"
    assert found_response, f"Yanıt logu bulunamadı (correlation_id: {correlation_id})"


def test_audit_logging():
    """
    Test: AuditLogger çalışıyor mu?
    Beklenti: audit.log dosyasına doğru formatta kayıt düşmeli.
    """
    audit = get_audit_logger()
    test_event_id = str(uuid.uuid4())
    test_user = "test_admin"

    # Audit kaydı oluştur
    audit.log(
        event="TEST_VERIFICATION",
        user=test_user,
        details={"verification_id": test_event_id, "note": "Loglama sistemi kontrolü"},
        status="SUCCESS",
    )

    # Audit dosyasını kontrol et
    audit_file = LOG_DIR / "audit.log"
    assert audit_file.exists()

    found_audit = False
    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f.readlines():  # Son satırlara bakmak yeterli olur ama basitçe oku
            if test_event_id in line:
                try:
                    log_entry = json.loads(line)
                    if (
                        log_entry.get("audit_event") == "TEST_VERIFICATION"
                        and log_entry.get("actor") == test_user
                    ):
                        found_audit = True
                        assert log_entry["details"]["verification_id"] == test_event_id
                except:
                    pass

    assert found_audit, "Audit log kaydı bulunamadı veya format hatalı"
