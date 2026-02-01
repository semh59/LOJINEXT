"""
TIR Yakıt Takip - Model Manager
Model versiyonlama, karşılaştırma ve rollback
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

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

    def save_version(
        self,
        arac_id: int,
        model_type: ModelType,
        params: Dict,
        metrics: Dict,
        notes: str = ""
    ) -> int:
        """
        Yeni model versiyonu kaydet.
        
        Args:
            arac_id: Araç ID
            model_type: Model tipi
            params: Model parametreleri
            metrics: Performans metrikleri (r2, mae, sample_count)
            notes: Notlar
            
        Returns:
            Version ID
        """
        with get_connection() as conn:
            # Mevcut en yüksek versiyon numarasını bul
            row = conn.execute("""
                SELECT MAX(version) FROM model_versions 
                WHERE arac_id = ? AND model_type = ?
            """, (arac_id, model_type.value)).fetchone()

            next_version = (row[0] or 0) + 1

            # Yeni versiyonu kaydet
            cursor = conn.execute("""
                INSERT INTO model_versions 
                (arac_id, version, model_type, params_json, r2_score, mae, sample_count, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                arac_id,
                next_version,
                model_type.value,
                json.dumps(params),
                metrics.get('r2_score'),
                metrics.get('mae'),
                metrics.get('sample_count', 0),
                notes
            ))

            version_id = cursor.lastrowid

            # Bu versiyonu aktif yap
            self.activate_version(version_id, conn=conn)

            # Eski versiyonları temizle (MAX_VERSIONS'dan fazlasını sil)
            self._cleanup_old_versions(arac_id, model_type, conn)

            logger.info(f"Saved model version {next_version} for vehicle {arac_id}")
            return version_id

    def activate_version(
        self,
        version_id: int,
        conn=None
    ) -> bool:
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
                "SELECT arac_id, model_type FROM model_versions WHERE id = ?",
                (version_id,)
            ).fetchone()

            if not row:
                return False

            arac_id, model_type = row['arac_id'], row['model_type']

            # Atomik UPDATE: Tek sorgu ile tüm versiyonları güncelle
            # Bu, SELECT + UPDATE + UPDATE yerine tek atomik işlem sağlar
            conn.execute("""
                UPDATE model_versions 
                SET is_active = CASE WHEN id = ? THEN 1 ELSE 0 END
                WHERE arac_id = ? AND model_type = ?
            """, (version_id, arac_id, model_type))

            if owns_connection:
                conn.commit()

            logger.info(f"Activated model version {version_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to activate version: {e}")
            if owns_connection and conn:
                try:
                    conn.rollback()
                except Exception:
                    pass  # Rollback hatası loglama - connection zaten bozuk olabilir
            return False
        finally:
            # CONNECTION LEAK FIX: Her durumda connection'ı kapat
            if owns_connection and connection_context is not None:
                try:
                    connection_context.__exit__(None, None, None)
                except Exception as cleanup_error:
                    logger.warning(f"Connection cleanup error: {cleanup_error}")

    def get_active_version(
        self,
        arac_id: int,
        model_type: ModelType
    ) -> Optional[ModelVersion]:
        """Aktif model versiyonunu getir"""
        with get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM model_versions 
                WHERE arac_id = ? AND model_type = ? AND is_active = 1
            """, (arac_id, model_type.value)).fetchone()

            if row:
                return self._row_to_model(dict(row))
        return None

    def get_versions(
        self,
        arac_id: int,
        model_type: ModelType = None
    ) -> List[ModelVersion]:
        """Araç için tüm versiyonları getir"""
        with get_connection() as conn:
            query = "SELECT * FROM model_versions WHERE arac_id = ?"
            params = [arac_id]

            if model_type:
                query += " AND model_type = ?"
                params.append(model_type.value)

            query += " ORDER BY created_at DESC"

            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._row_to_model(dict(row)) for row in rows]

    def rollback_to_version(self, version_id: int) -> bool:
        """Eski bir versiyona geri dön"""
        return self.activate_version(version_id)

    def compare_versions(
        self,
        version_id_1: int,
        version_id_2: int
    ) -> Dict:
        """İki versiyonu karşılaştır"""
        with get_connection() as conn:
            v1 = conn.execute(
                "SELECT * FROM model_versions WHERE id = ?", (version_id_1,)
            ).fetchone()
            v2 = conn.execute(
                "SELECT * FROM model_versions WHERE id = ?", (version_id_2,)
            ).fetchone()

            if not v1 or not v2:
                return {'error': 'Version not found'}

            v1, v2 = dict(v1), dict(v2)

            return {
                'version_1': {
                    'id': v1['id'],
                    'version': v1['version'],
                    'r2_score': v1['r2_score'],
                    'mae': v1['mae'],
                    'sample_count': v1['sample_count'],
                    'created_at': v1['created_at']
                },
                'version_2': {
                    'id': v2['id'],
                    'version': v2['version'],
                    'r2_score': v2['r2_score'],
                    'mae': v2['mae'],
                    'sample_count': v2['sample_count'],
                    'created_at': v2['created_at']
                },
                'comparison': {
                    'r2_diff': (v2['r2_score'] or 0) - (v1['r2_score'] or 0),
                    'mae_diff': (v2['mae'] or 0) - (v1['mae'] or 0),
                    'sample_diff': (v2['sample_count'] or 0) - (v1['sample_count'] or 0)
                }
            }

    def delete_version(self, version_id: int) -> bool:
        """Versiyonu sil (aktif değilse)"""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT is_active FROM model_versions WHERE id = ?",
                (version_id,)
            ).fetchone()

            if not row:
                return False

            if row['is_active']:
                logger.warning("Cannot delete active version")
                return False

            conn.execute("DELETE FROM model_versions WHERE id = ?", (version_id,))
            logger.info(f"Deleted model version {version_id}")
            return True

    def _cleanup_old_versions(
        self,
        arac_id: int,
        model_type: ModelType,
        conn
    ):
        """Eski versiyonları temizle"""
        # Aktif olmayan ve en eski olanları bul
        rows = conn.execute("""
            SELECT id FROM model_versions 
            WHERE arac_id = ? AND model_type = ? AND is_active = 0
            ORDER BY created_at DESC
            LIMIT -1 OFFSET ?
        """, (arac_id, model_type.value, self.MAX_VERSIONS - 1)).fetchall()

        for row in rows:
            conn.execute("DELETE FROM model_versions WHERE id = ?", (row['id'],))
            logger.debug(f"Cleaned up old version {row['id']}")

    def _row_to_model(self, row: Dict) -> ModelVersion:
        """Row'u ModelVersion'a dönüştür"""
        return ModelVersion(
            id=row['id'],
            arac_id=row['arac_id'],
            version=row['version'],
            model_type=ModelType(row['model_type']),
            params_json=row['params_json'],
            r2_score=row['r2_score'],
            mae=row['mae'],
            sample_count=row['sample_count'] or 0,
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            notes=row.get('notes')
        )


# Singleton (Thread-Safe Double-Checked Locking)
import threading
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
