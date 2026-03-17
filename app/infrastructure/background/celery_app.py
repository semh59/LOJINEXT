# -*- coding: utf-8 -*-
"""
Celery uygulama tanımı.
Redis broker/backend varsayılan; prod için env zorunlu (settings validator).
"""

from celery import Celery
from app.config import settings

def get_celery_app() -> Celery:
    """
    Celery uygulamasını hazırlar.

    settings.CELERY_EAGER=True ise bellek broker/backend kullanılır ve
    görevler yayıncı süreçte senkron çalışır (dev/test).
    """
    if settings.CELERY_EAGER:
        broker = "memory://"
        backend = "cache+memory://"
    else:
        broker = settings.CELERY_BROKER_URL or "redis://localhost:6379/0"
        backend = settings.CELERY_RESULT_BACKEND or broker

    app = Celery("lojinext", broker=broker, backend=backend)
    app.conf.update(
        task_soft_time_limit=70,
        task_time_limit=90,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        broker_transport_options={"visibility_timeout": 120},
        beat_schedule={
            "drain-prediction-dlq-every-60s": {
                "task": "prediction.drain_dlq",
                "schedule": 60.0,
            }
        },
        worker_hostname="lojinext-worker@%h",
        task_always_eager=settings.CELERY_EAGER,
        task_eager_propagates=settings.CELERY_EAGER,
    )
    return app


celery_app = get_celery_app()

# Ensure tasks are registered
import app.workers.tasks.prediction_tasks  # noqa: E402,F401
import app.workers.tasks.dlq_tasks  # noqa: E402,F401
