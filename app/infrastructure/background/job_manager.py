"""
Async Background Job Manager
External dependency gerektirmeden (Celery vb. olmadan)
native asyncio kullanarak arka plan görevlerini yönetir.
"""

import asyncio
import uuid
import logging
from typing import Callable, Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BackgroundJobManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackgroundJobManager, cls).__new__(cls)
            cls._instance._tasks: Dict[str, asyncio.Task] = {}
            cls._instance._results: Dict[str, Any] = {}
            cls._instance._status: Dict[str, str] = {} # pending, running, completed, failed
            cls._instance._errors: Dict[str, str] = {}
        return cls._instance

    async def submit(self, func: Callable, *args, **kwargs) -> str:
        """
        Arka plana bir görev gönderir.
        
        Args:
            func: Çalıştırılacak async fonksiyon
            *args, **kwargs: Fonksiyon parametreleri
            
        Returns:
            job_id: Görevin benzersiz ID'si
        """
        job_id = str(uuid.uuid4())
        self._status[job_id] = "pending"
        
        # Wrapper to handle execution and result storage
        async def _wrapper():
            self._status[job_id] = "running"
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                self._results[job_id] = result
                self._status[job_id] = "completed"
                logger.info(f"Job {job_id} completed successfully.")
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                self._status[job_id] = "failed"
                self._errors[job_id] = str(e)
            finally:
                # Cleanup task reference after delay to free memory (optional logic)
                # For now we keep it to verify status
                pass

        # Create background task
        task = asyncio.create_task(_wrapper())
        self._tasks[job_id] = task
        
        return job_id

    def get_status(self, job_id: str) -> Dict[str, Any]:
        """Görevin durumunu sorgula"""
        return {
            "id": job_id,
            "status": self._status.get(job_id, "unknown"),
            "result": self._results.get(job_id),
            "error": self._errors.get(job_id),
            "timestamp": datetime.now().isoformat()
        }

    def cleanup(self, max_age_seconds: int = 3600):
        """Eski görev kayıtlarını temizle"""
        # TODO: Implement periodic cleanup
        pass

# Singleton factory
def get_job_manager() -> BackgroundJobManager:
    return BackgroundJobManager()
