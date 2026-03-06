"""
TIR Yakıt Takip - Model Manager
Model versiyonlama, karşılaştırma ve rollback
"""

import json
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy import text  # Added import

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.database.connection import get_connection
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class ModelType(str, Enum):
    """Model tipleri"""

    ENSEMBLE = "ensemble"
    KALMAN = "kalman"
    PHYSICS = "physics"


@dataclass
class ModelVersion:
    """Model versiyonu"""

    id: int
    arac_id: int
    version: int
    model_type: ModelType
    params_json: str
    r2_score: Optional[float]
    mae: Optional[float]
    sample_count: int
    is_active: bool
    created_at: datetime
    notes: Optional[str] = None


class ModelManager:
    """
    Model versiyonlama ve yönetim.

    Özellikler:
    - Versiyon kaydetme
    - Aktif versiyon yönetimi
    - Versiyon karşılaştırma
    - Rollback
    """

    MAX_VERSIONS = 5  # Araç başına tutulacak maksimum versiyon

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, "item"):
                return obj.item()
            if hasattr(obj, "tolist"):
                return obj.tolist()
            return super().default(obj)

    def save_version(
        self,
        arac_id: int,
        model_type: ModelType,
        params: Dict,
        metrics: Dict,
        notes: str = "",
    ) -> int:
        """New model version save with Numpy support."""
        logger.info(f"Saving version for arac_id={arac_id} type={model_type}")
        with get_connection() as conn:
            # Get max version
            row = conn.execute(
                text("""
                SELECT MAX(version) FROM model_versions 
                WHERE arac_id = CAST(:arac_id AS INTEGER) AND model_type = :model_type
            """),
                {"arac_id": arac_id, "model_type": model_type.value},
            ).fetchone()

            next_version = (row[0] or 0) + 1

            # Insert
            params_json = json.dumps(params, cls=self.NumpyEncoder)

            # Sanitize metrics (convert numpy types to python native)
            def to_native(val):
                if hasattr(val, "item"):
                    return val.item()
                return val

            cursor = conn.execute(
                text("""
                INSERT INTO model_versions 
                (arac_id, version, model_type, params_json, r2_score, mae, sample_count, is_active, notes)
                VALUES (:arac_id, :version, :model_type, :params_json, :r2_score, :mae, :sample_count, :is_active, :notes)
                RETURNING id
            """),
                {
                    "arac_id": arac_id,
                    "version": next_version,
                    "model_type": model_type.value,
                    "params_json": params_json,
                    "r2_score": to_native(
                        metrics.get("ensemble_r2")
                        or metrics.get("r2_score")
                        or metrics.get("r2")
                        # Fallback to top level of metrics if it's passed that way
                        or metrics.get("metrics", {}).get("ensemble_r2")
                        or 0.0
                    ),
                    "mae": to_native(
                        metrics.get("mae")
                        or metrics.get("measurements", {}).get("mae")
                        or metrics.get("physics_mae")
                    ),
                    "sample_count": to_native(metrics.get("sample_count", 0)),
                    "is_active": False,
                    "notes": notes,
                },
            )

            version_id = cursor.fetchone()[0]

            # Bu versiyonu aktif yap
            self.activate_version(version_id, conn=conn)

            # Eski versiyonları temizle (MAX_VERSIONS'dan fazlasını sil)
            self._cleanup_old_versions(arac_id, model_type, conn)

            logger.info(f"Saved model version {next_version} for vehicle {arac_id}")
            return version_id

    def activate_version(self, version_id: int, conn=None) -> bool:
        """
        Belirli bir versiyonu aktif yap.

        CONNECTION LEAK FIX: Proper context manager kullanımı.
        TOCTOU FIX: Atomik UPDATE sorgusu ile race condition önleme.
        """
        owns_connection = conn is None
        connection_context = None

        try:
            if owns_connection:
                connection_context = get_connection()
                conn = connection_context.__enter__()

            # TOCTOU FIX: Atomik UPDATE - tek sorgu ile tüm işlemi yap
            # Önce version_id'nin geçerli olduğunu kontrol et
            row = conn.execute(
                text("SELECT arac_id, model_type FROM model_versions WHERE id = :id"),
                {"id": version_id},
            ).fetchone()

            if not row:
                return False

            arac_id, model_type = row[0], row[1]

            # Atomik UPDATE: Tek sorgu ile tüm versiyonları güncelle
            conn.execute(
                text("""
                UPDATE model_versions 
                SET is_active = CASE WHEN id = :id THEN CAST(:true_val AS BOOLEAN) ELSE CAST(:false_val AS BOOLEAN) END
                WHERE arac_id = CAST(:arac_id AS INTEGER) AND model_type = :model_type
            """),
                {
                    "id": version_id,
                    "arac_id": arac_id,
                    "model_type": model_type,
                    "true_val": True,
                    "false_val": False,
                },
            )

            if owns_connection:
                conn.commit()

            logger.info(f"Activated model version {version_id}")
            return True

        except Exception as e:
            # ... (keep existing exception handling)
            logger.error(f"Failed to activate version: {e}")
            if owns_connection and conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            return False
        finally:
            if owns_connection and connection_context is not None:
                try:
                    connection_context.__exit__(None, None, None)
                except Exception:
                    pass

    def get_active_version(
        self, arac_id: int, model_type: ModelType
    ) -> Optional[ModelVersion]:
        """Aktif model versiyonunu getir"""
        with get_connection() as conn:
            row = conn.execute(
                text("""
                SELECT * FROM model_versions 
                WHERE arac_id = CAST(:arac_id AS INTEGER) AND model_type = :model_type AND is_active = CAST(:is_active_val AS BOOLEAN)
            """),
                {
                    "arac_id": arac_id,
                    "model_type": model_type.value,
                    "is_active_val": True,
                },
            ).fetchone()

            if row:
                return self._row_to_model(dict(row._mapping))
        return None

    # ... get_versions ...

    def delete_version(self, version_id: int) -> bool:
        """Versiyonu sil (aktif değilse)"""
        with get_connection() as conn:
            row = conn.execute(
                text("SELECT is_active FROM model_versions WHERE id = :id"),
                {"id": version_id},
            ).fetchone()

            if not row:
                return False

            if row[0]:  # is_active
                logger.warning("Cannot delete active version")
                return False

            conn.execute(
                text("DELETE FROM model_versions WHERE id = :id"), {"id": version_id}
            )
            logger.info(f"Deleted model version {version_id}")
            return True

    def _cleanup_old_versions(self, arac_id: int, model_type: ModelType, conn):
        """Eski versiyonları temizle"""
        # Aktif olmayan ve en eski olanları bul
        rows = conn.execute(
            text("""
            SELECT id FROM model_versions 
            WHERE arac_id = CAST(:arac_id AS INTEGER) AND model_type = :model_type AND is_active = CAST(:is_active_val AS BOOLEAN)
            ORDER BY created_at DESC
            OFFSET :offset
        """),
            {
                "arac_id": arac_id,
                "model_type": model_type.value,
                "offset": self.MAX_VERSIONS - 1,
                "is_active_val": False,
            },
        ).fetchall()

        for row in rows:
            conn.execute(
                text("DELETE FROM model_versions WHERE id = :id"), {"id": row.id}
            )
            logger.debug(f"Cleaned up old version {row['id']}")

    def _row_to_model(self, row: Dict) -> ModelVersion:
        """Row'u ModelVersion'a dönüştür"""
        return ModelVersion(
            id=row["id"],
            arac_id=row["arac_id"],
            version=row["version"],
            model_type=ModelType(row["model_type"]),
            params_json=row["params_json"],
            r2_score=row["r2_score"],
            mae=row["mae"],
            sample_count=row["sample_count"] or 0,
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"])
            if isinstance(row["created_at"], str)
            else row["created_at"],
            feature_schema_hash=row.get("feature_schema_hash"),
            training_data_hash=row.get("training_data_hash"),
            physics_version=row.get("physics_version"),
            notes=row.get("notes"),
        )


# Singleton (Thread-Safe Double-Checked Locking)
_model_manager = None
_model_manager_lock = threading.Lock()


def get_model_manager() -> ModelManager:
    """Thread-safe singleton erişimi"""
    global _model_manager
    if _model_manager is None:
        with _model_manager_lock:
            if _model_manager is None:  # Double-checked locking
                _model_manager = ModelManager()
    return _model_manager
