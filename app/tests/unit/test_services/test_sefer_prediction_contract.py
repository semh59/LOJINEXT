import numpy as np

from app.core.ml.ensemble_predictor import EnsembleFuelPredictor
from app.core.services.sefer_write_service import SeferWriteService
from app.database.repositories.audit_repo import AuditRepository


def test_extract_prediction_values_prefers_canonical_field():
    service = SeferWriteService()
    value, meta = service._extract_prediction_values(
        {
            "tahmini_tuketim": 32.4,
            "prediction_liters": 999.0,
            "model_used": "ensemble",
            "model_version": "ensemble-v2",
            "confidence_score": 0.82,
        },
        quality_flags={"route_available": True},
    )

    assert value == 32.4
    assert meta is not None
    assert meta["model_used"] == "ensemble"
    assert meta["model_version"] == "ensemble-v2"
    assert meta["input_quality"]["route_available"] is True


def test_extract_prediction_values_rejects_alias_only_payload():
    service = SeferWriteService()
    value, meta = service._extract_prediction_values(
        {
            "prediction_liters": 41.7,
            "model_used": "physics",
        }
    )

    assert value is None
    assert meta is None


def test_timeline_event_type_normalization_prediction_refresh():
    event_type = AuditRepository._normalize_event_type(
        "UPDATE",
        [{"alan": "tahmini_tuketim", "eski": 30.1, "yeni": 31.0}],
    )
    assert event_type == "PREDICTION_REFRESH"


def test_timeline_event_type_normalization_status_change():
    event_type = AuditRepository._normalize_event_type(
        "UPDATE",
        [{"alan": "durum", "eski": "Bekliyor", "yeni": "Yolda"}],
    )
    assert event_type == "STATUS_CHANGE"


class _DummyModel:
    def __init__(self, n_features_in_: int):
        self.n_features_in_ = n_features_in_


def test_ensemble_feature_alignment_truncates_for_legacy_model():
    predictor = EnsembleFuelPredictor()
    predictor.scaler = _DummyModel(n_features_in_=24)
    X = np.ones((1, 26), dtype=float)

    aligned = predictor._align_feature_matrix(X)

    assert aligned.shape == (1, 24)


def test_ensemble_feature_alignment_pads_when_runtime_has_fewer_features():
    predictor = EnsembleFuelPredictor()
    predictor.scaler = _DummyModel(n_features_in_=26)
    X = np.ones((1, 24), dtype=float)

    aligned = predictor._align_feature_matrix(X)

    assert aligned.shape == (1, 26)
    assert aligned[0, -1] == 0.0
