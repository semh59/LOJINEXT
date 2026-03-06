"""
Audit Logging Decorator - Kritik işlemler için audit trail
SERVIS LAYER AUDIT - Bulgu 8 düzeltmesi
"""

import functools
import json
from datetime import datetime, timezone
from typing import Callable

from app.infrastructure.logging.logger import get_logger

audit_logger = get_logger("audit")


def audit_log(action: str, entity_type: str = None, log_params: bool = False):
    """
    Kritik işlemler için audit log decorator.

    WHO, WHAT, WHEN, WHERE bilgilerini loglar.

    Args:
        action: İşlem tipi (CREATE, UPDATE, DELETE, READ)
        entity_type: Entity tipi (sefer, arac, sofor, yakit)
        log_params: Parametreleri logla (sensitive olmayan)

    Usage:
        @audit_log("CREATE", "sefer")
        async def add_sefer(self, data: SeferCreate):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = datetime.now(timezone.utc)

            # User ID çıkarma girişimi
            user_id = kwargs.get("user_id")
            if not user_id and len(args) > 0:
                user_id = getattr(args[0], "_current_user_id", None)

            audit_entry = {
                "timestamp": start.isoformat(),
                "action": action,
                "entity": entity_type or func.__name__,
                "user_id": user_id,
                "function": func.__name__,
                "status": "started",
            }

            if log_params and kwargs:
                from app.infrastructure.security.pii_scrubber import scrub_pii

                safe_params = scrub_pii(kwargs)
                audit_entry["params"] = str(safe_params)[:500]

            try:
                result = await func(*args, **kwargs)
                audit_entry["status"] = "success"
                audit_entry["duration_ms"] = round(
                    (datetime.now(timezone.utc) - start).total_seconds() * 1000, 2
                )
                audit_logger.info(json.dumps(audit_entry, default=str))
                return result
            except Exception as e:
                audit_entry["status"] = "failed"
                audit_entry["error"] = str(e)[:200]
                audit_entry["duration_ms"] = round(
                    (datetime.now(timezone.utc) - start).total_seconds() * 1000, 2
                )
                audit_logger.error(json.dumps(audit_entry, default=str))
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = datetime.now(timezone.utc)

            audit_entry = {
                "timestamp": start.isoformat(),
                "action": action,
                "entity": entity_type or func.__name__,
                "function": func.__name__,
                "status": "started",
            }

            try:
                result = func(*args, **kwargs)
                audit_entry["status"] = "success"
                audit_entry["duration_ms"] = round(
                    (datetime.now(timezone.utc) - start).total_seconds() * 1000, 2
                )
                audit_logger.info(json.dumps(audit_entry, default=str))
                return result
            except Exception as e:
                audit_entry["status"] = "failed"
                audit_entry["error"] = str(e)[:200]
                audit_entry["duration_ms"] = round(
                    (datetime.now(timezone.utc) - start).total_seconds() * 1000, 2
                )
                audit_logger.error(json.dumps(audit_entry, default=str))
                raise

        # Async veya sync fonksiyon mu?
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
