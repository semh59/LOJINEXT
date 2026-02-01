"""
TIR Yakıt Takip Sistemi - Migration Manager

DEPRECATED: Bu modül legacy SQLite migration'ları içindir.
PostgreSQL için Alembic kullanın: `alembic upgrade head`
"""

import logging
import sys
import warnings
from pathlib import Path
from typing import List

from app.infrastructure.logging.logger import get_logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = get_logger(__name__)

class MigrationManager:
    """
    DEPRECATED: Legacy SQLite migration manager.
    PostgreSQL için Alembic kullanın: `alembic upgrade head`
    """
    MIGRATIONS_DIR = Path(__file__).parent / "sql"

    def __init__(self):
        warnings.warn(
            "MigrationManager is DEPRECATED. Use Alembic for PostgreSQL migrations: "
            "`alembic upgrade head`",
            DeprecationWarning,
            stacklevel=2
        )
        self._ensure_version_table()
    
    def _ensure_version_table(self):
        """Schema version tablosunu oluştur"""
        from app.database.connection import get_sync_session
        from sqlalchemy import text
        
        with get_sync_session() as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """))
            
            # Eğer boşsa 0 olarak başlat
            version_count = session.execute(text("SELECT COUNT(*) FROM schema_version")).scalar()
            if version_count == 0:
                session.execute(text("INSERT INTO schema_version (version, description) VALUES (0, 'Initial')"))
                session.commit()
    
    def get_current_version(self) -> int:
        """Mevcut DB versiyonunu al"""
        from app.database.connection import get_sync_session
        from sqlalchemy import text
        
        with get_sync_session() as session:
            version = session.execute(text("SELECT MAX(version) FROM schema_version")).scalar()
            return version if version is not None else 0
    
    def get_pending_migrations(self) -> List[Path]:
        """Bekleyen migration dosyalarını bul"""
        current_version = self.get_current_version()
        files = sorted(self.MIGRATIONS_DIR.glob("*.sql"))
        
        pending = []
        for f in files:
            try:
                # Dosya adı formatı: 001_initial.sql
                parts = f.name.split('_')
                if not parts[0].isdigit():
                    continue
                    
                version = int(parts[0])
                if version > current_version:
                    pending.append(f)
            except ValueError:
                logger.warning(f"Invalid migration file format: {f.name}")
        
        return pending
    
    def apply_migrations(self):
        """Pending migration'ları uygula"""
        pending = self.get_pending_migrations()
        if not pending:
            logger.info("No pending migrations.")
            return
            
        logger.info(f"Found {len(pending)} pending migrations.")
        
        for migration_file in pending:
            parts = migration_file.name.split('_')
            version = int(parts[0])
            logger.info(f"Applying migration {version}: {migration_file.name}")
            
            try:
                self._apply_migration_file(migration_file, version)
                logger.info(f"Successfully applied migration {version}")
            except Exception as e:
                logger.error(f"Failed to apply migration {version}: {e}")
                raise
    
    def _apply_migration_file(self, file_path: Path, version: int):
        """Tek bir migration dosyasını uygula"""
        from app.database.connection import get_sync_session
        from sqlalchemy import text
        
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        # Basit statement ayırıcı (complex trigger/function tanımları için yetersiz olabilir
        # ama basit migrationlar için yeterli)
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        with get_sync_session() as session:
            # Transaction içinde çalıştır
            for statement in statements:
                session.execute(text(statement))
            
            # Versiyonu güncelle
            description = file_path.stem
            session.execute(
                text("INSERT INTO schema_version (version, description) VALUES (:version, :desc)"),
                {"version": version, "desc": description}
            )
            session.commit()

if __name__ == "__main__":
    # Setup basic logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    manager = MigrationManager()
    manager.apply_migrations()

