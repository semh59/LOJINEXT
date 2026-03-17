from pathlib import Path

from app.core.services.sefer_write_service import SeferWriteService
from app.schemas.sefer import SeferDurum


EXPECTED_STATUS_SET = {
    "Bekliyor",
    "Planlandı",
    "Yolda",
    "Devam Ediyor",
    "Tamamlandı",
    "Tamam",
    "İptal",
}


def test_status_literal_set_is_single_source_of_truth():
    schema_values = set(SeferDurum.__args__)
    assert schema_values == EXPECTED_STATUS_SET

    transition_values = set(SeferWriteService.VALID_STATUS_TRANSITIONS.keys())
    assert transition_values == EXPECTED_STATUS_SET

    for _, allowed in SeferWriteService.VALID_STATUS_TRANSITIONS.items():
        assert set(allowed).issubset(EXPECTED_STATUS_SET)


def test_runtime_contract_files_do_not_use_legacy_ascii_status_literals():
    root = Path(__file__).resolve().parents[3]
    checked_files = [
        root / "app" / "schemas" / "sefer.py",
        root / "app" / "core" / "services" / "sefer_write_service.py",
        root / "app" / "database" / "repositories" / "sefer_repo.py",
    ]
    legacy_ascii_statuses = ["Iptal", "Planlandi", "Tamamlandi"]

    for file_path in checked_files:
        if not file_path.exists():
            continue
        content = file_path.read_text(encoding="utf-8")
        for token in legacy_ascii_statuses:
            assert token not in content, f"{file_path} still contains legacy token: {token}"


def test_legacy_ascii_aliases_exist_only_in_normalizer():
    root = Path(__file__).resolve().parents[3]
    normalizer_file = root / "app" / "core" / "utils" / "sefer_status.py"
    content = normalizer_file.read_text(encoding="utf-8")

    for token in ("Iptal", "Planlandi", "Tamamlandi"):
        assert token in content
