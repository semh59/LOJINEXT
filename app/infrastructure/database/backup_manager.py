import os
import subprocess
import logging
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseBackupManager:
    """
    Handles PostgreSQL database backups and retention.
    """
    def __init__(self):
        self.backup_dir = "storage/backups"
        self.db_host = settings.DB_HOST
        self.db_user = settings.POSTGRES_USER
        self.db_name = settings.POSTGRES_DB
        self.retention_days = settings.BACKUP_RETENTION_DAYS
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self) -> str:
        """Creates a timestamped database dump."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.db_name}_{timestamp}.sql"
        filepath = os.path.join(self.backup_dir, filename)
        
        # Note: In a containerized environment, PGPASSWORD env var should be set 
        # or a .pgpass file used. Here we assume the env is correctly configured.
        cmd = [
            "pg_dump",
            "-h", self.db_host,
            "-U", self.db_user,
            "-F", "p",  # Plain text format
            "-f", filepath,
            self.db_name
        ]
        
        try:
            logger.info(f"Starting backup: {filename}")
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Backup completed successfully: {filepath}")
            return filepath
        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during backup: {e}")
            raise

    def cleanup_old_backups(self):
        """Removes backups older than the retention threshold."""
        now = datetime.now()
        threshold = now - timedelta(days=self.retention_days)
        
        for filename in os.listdir(self.backup_dir):
            if not filename.endswith(".sql"):
                continue
                
            filepath = os.path.join(self.backup_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if file_time < threshold:
                try:
                    os.remove(filepath)
                    logger.info(f"Deleted old backup: {filename}")
                except Exception as e:
                    logger.error(f"Failed to delete {filename}: {e}")

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    manager = DatabaseBackupManager()
    if "--test" in sys.argv:
        try:
            manager.create_backup()
            manager.cleanup_old_backups()
        except Exception:
            sys.exit(1)
