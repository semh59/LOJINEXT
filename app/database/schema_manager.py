import os

import app.database.connection as db_conn
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class SchemaManager:
    """Veritabanı şema ve başlangıç verilerini yönetir."""

    @staticmethod
    def init_database():
        """
        [DEPRECATED] SQLite Tablolarını oluşturur.
        POSTGRESQL GEÇİŞİ TAMAMLANMIŞTIR. 
        Bu metod artık tablo oluşturmaz. Tüm şema değişiklikleri Alembic üzerinden yapılmalıdır.
        """
        logger.warning("SchemaManager.init_database() is DEPRECATED and INACTIVE.")
        logger.info("Please use 'alembic upgrade head' for database schema management.")
        
        # Explicitly check for migration environment
        if os.getenv("ALLOW_SCHEMA_INIT", "false").lower() == "true":
             logger.critical("ALLOW_SCHEMA_INIT is set to true but SchemaManager no longer supports direct initialization. Use Alembic.")

    # REMOVED: _create_default_admin (Legacy)
    # REMOVED: _insert_demo_data (Legacy)
