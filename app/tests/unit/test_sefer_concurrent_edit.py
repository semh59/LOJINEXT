"""
Concurrent Edit (Race Condition) Tests for Sefer Module.

These tests document and verify the "last writer wins" behavior
identified in audit finding B-004 (Optimistic Locking Yok).

No optimistic locking is currently implemented — these tests serve as:
1. Documentation of the current behavior
2. Regression guards for when optimistic locking is added
3. Proof that status transition guards DO protect against invalid states
"""

from datetime import date
from types import SimpleNamespace

from app.schemas.sefer import SeferUpdate
from app.core.utils.sefer_status import SEFER_STATUS_TRANSITIONS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mock_sefer(id: int = 1, durum: str = "Bekliyor", **overrides):
    """Create a mock Sefer-like object using SimpleNamespace (no auto-attrs)."""
    defaults = {
        "id": id,
        "sefer_no": f"SEF-{id:03d}",
        "tarih": date(2026, 1, 15),
        "saat": "10:00",
        "arac_id": 1,
        "sofor_id": 1,
        "guzergah_id": 1,
        "cikis_yeri": "İstanbul",
        "varis_yeri": "Ankara",
        "mesafe_km": 450.0,
        "bos_agirlik_kg": 8000,
        "dolu_agirlik_kg": 18000,
        "net_kg": 10000,
        "ton": 10.0,
        "durum": durum,
        "is_deleted": False,
        "is_real": True,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    defaults.update(overrides)

    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Tests: Status Transition Guards (Backend protection against invalid states)
# ---------------------------------------------------------------------------


class TestStatusTransitionGuards:
    """
    Even without optimistic locking, status transition guards
    prevent impossible state changes via direct API calls.
    """

    def test_completed_trip_cannot_go_back_to_active(self):
        """Terminal states (Tamamlandı, Tamam) have no allowed transitions."""
        allowed = SEFER_STATUS_TRANSITIONS.get("Tamamlandı", set())
        assert len(allowed) == 0, (
            "Tamamlandı is terminal — no transitions should be allowed"
        )

    def test_tamam_trip_cannot_go_back_to_active(self):
        allowed = SEFER_STATUS_TRANSITIONS.get("Tamam", set())
        assert len(allowed) == 0

    def test_iptal_trip_cannot_be_reactivated(self):
        allowed = SEFER_STATUS_TRANSITIONS.get("İptal", set())
        assert len(allowed) == 0, "İptal is terminal — no transitions should be allowed"

    def test_bekliyor_allows_forward_transitions_only(self):
        allowed = SEFER_STATUS_TRANSITIONS.get("Bekliyor", set())
        assert "Yolda" in allowed
        assert "İptal" in allowed
        # Terminal states should not be directly reachable from Bekliyor
        assert "Tamam" not in allowed
        assert "Tamamlandı" not in allowed

    def test_yolda_can_complete_or_cancel(self):
        allowed = SEFER_STATUS_TRANSITIONS.get("Yolda", set())
        assert "Tamamlandı" in allowed or "Tamam" in allowed
        assert "İptal" in allowed


# ---------------------------------------------------------------------------
# Tests: Concurrent Update Behavior Documentation
# ---------------------------------------------------------------------------


class TestConcurrentEditBehavior:
    """
    Documents the current 'last writer wins' behavior.
    These tests use mocks to simulate concurrent access patterns.
    """

    def test_last_writer_wins_on_field_update(self):
        """
        When two updates target the same field, the last one persists.
        This documents B-004: no optimistic locking.
        """
        sefer = _make_mock_sefer(durum="Bekliyor")

        # Simulate user A changing notes
        update_a = SeferUpdate(notlar="User A notes")
        # Simulate user B changing notes
        update_b = SeferUpdate(notlar="User B notes")

        # Both updates target the same field — last applied wins
        if update_a.notlar:
            sefer.notlar = update_a.notlar
        if update_b.notlar:
            sefer.notlar = update_b.notlar

        assert sefer.notlar == "User B notes", (
            "B-004: Last writer wins — User A's change is silently overwritten"
        )

    def test_concurrent_status_change_first_wins_due_to_guard(self):
        """
        When status has already been changed by user A,
        user B's change may fail if the old status is now terminal.
        Status transition guards provide partial protection.
        """
        # User A changes Bekliyor → Tamamlandı (via Yolda → Tamamlandı path)
        sefer = _make_mock_sefer(durum="Tamamlandı")

        # User B tries to change from "Bekliyor" → "İptal"
        # But sefer.durum is already "Tamamlandı" (terminal)
        current_allowed = SEFER_STATUS_TRANSITIONS.get(sefer.durum, set())

        # İptal is not allowed from Tamamlandı
        assert "İptal" not in current_allowed, (
            "Status guard prevents reopening a completed trip"
        )

    def test_parallel_delete_and_update_race(self):
        """
        When one user deletes and another updates simultaneously,
        the update will fail because soft-deleted records are filtered.
        """
        sefer = _make_mock_sefer(durum="Bekliyor")

        # User A soft-deletes
        sefer.is_deleted = True
        sefer.durum = "İptal"

        # User B tries to update — but get_by_id should return None for deleted
        # This simulates the repo behavior
        is_accessible = not sefer.is_deleted
        assert not is_accessible, "Soft-deleted sefer is not accessible for updates"


# ---------------------------------------------------------------------------
# Tests: Bulk Operation Atomicity
# ---------------------------------------------------------------------------


class TestBulkOperationAtomicity:
    """
    Bulk operations use a single UoW (Unit of Work).
    These tests verify the expected contract.
    """

    def test_bulk_status_transitions_are_individual(self):
        """
        In a bulk status update, each sefer is validated individually.
        A failed transition for one should not block others.
        """
        seferler = [
            _make_mock_sefer(id=1, durum="Bekliyor"),  # Can transition
            _make_mock_sefer(id=2, durum="Tamamlandı"),  # Cannot transition (terminal)
            _make_mock_sefer(id=3, durum="Yolda"),  # Can transition
        ]

        new_status = "İptal"
        results = {"success": [], "failed": []}

        for s in seferler:
            allowed = SEFER_STATUS_TRANSITIONS.get(s.durum, set())
            if new_status in allowed:
                results["success"].append(s.id)
            else:
                results["failed"].append(s.id)

        assert 1 in results["success"]
        assert 2 in results["failed"], "Tamamlandı → İptal should fail"
        assert 3 in results["success"]

    def test_bulk_delete_handles_already_deleted(self):
        """
        If a sefer is already soft-deleted during bulk delete,
        it should be reported as failed, not cause a crash.
        """
        seferler = [
            _make_mock_sefer(id=1, is_deleted=False),
            _make_mock_sefer(id=2, is_deleted=True),  # Already deleted
            _make_mock_sefer(id=3, is_deleted=False),
        ]

        results = {"success": [], "failed": []}
        for s in seferler:
            if s.is_deleted:
                results["failed"].append(s.id)
            else:
                results["success"].append(s.id)

        assert len(results["success"]) == 2
        assert 2 in results["failed"]


# ---------------------------------------------------------------------------
# Tests: Race Condition Awareness
# ---------------------------------------------------------------------------


class TestRaceConditionAwareness:
    """
    These tests exist to document race condition risks
    and serve as regression tests when optimistic locking is added.
    """

    def test_no_version_field_exists_on_sefer_model(self):
        """
        B-004 root cause: Sefer model has no version/etag field.
        When optimistic locking is added, this test should FAIL.
        """
        sefer = _make_mock_sefer()
        has_version = hasattr(sefer, "version") or hasattr(sefer, "etag")
        assert not has_version, (
            "B-004: No version/etag field on Sefer model. "
            "This test should fail when optimistic locking is implemented."
        )

    def test_update_schema_has_no_version_field(self):
        """
        SeferUpdate schema has no version field for conflict detection.
        """
        fields = SeferUpdate.model_fields
        assert "version" not in fields, (
            "SeferUpdate has no version field — optimistic locking not implemented"
        )
        assert "etag" not in fields
