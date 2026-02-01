"""
Audit Logger - CRUD işlemlerini izler
Who, What, When, Where, Before/After state logging
"""

import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

from app.infrastructure.logging.logger import get_logger

# Correlation ID context variable (request bazlı)
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

logger = get_logger("audit")


def get_correlation_id() -> str:
    """Mevcut correlation ID'yi al veya oluştur"""
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid.uuid4())[:8]
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str):
    """Correlation ID'yi ayarla (middleware'den çağrılır)"""
    correlation_id_var.set(cid)


def audit_log(action: str, resource_type: str = ""):
    """
    Audit logging decorator.
    
    Args:
        action: İşlem tipi (CREATE, UPDATE, DELETE, READ vb.)
        resource_type: Kaynak tipi (VEHICLE, DRIVER, TRIP vb.)
    
    Kullanım:
        @audit_log("CREATE", "VEHICLE")
        async def create_arac(self, data: AracCreate) -> int:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            cid = get_correlation_id()
            
            # Hassas verileri maskelenmiş olarak hazırla
            # Args (genellikle ilk argüman 'self' olur, onu atla veya maskeli al)
            safe_args = [_mask_sensitive_data(a) if isinstance(a, (dict, list)) else a for a in args[1:]]
            # Sadece ilk 2 argümanı logla (performans ve temizlik için)
            safe_args_summary = safe_args[:2]
            
            safe_kwargs = _mask_sensitive_data(kwargs)
            # Sadece kwargs anahtarlarını logla (güvenlik için en sağlam yol)
            kwargs_summary = list(safe_kwargs.keys())
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                # Başarılı audit log
                logger.info(
                    f"AUDIT | {action} | {resource_type} | "
                    f"cid={cid} | "
                    f"args={safe_args_summary} | "
                    f"kwargs_keys={kwargs_summary} | "
                    f"success=True | "
                    f"duration={duration:.3f}s | "
                    f"result_id={_extract_id(result)}"
                )
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                # Hatalı audit log
                logger.error(
                    f"AUDIT | {action} | {resource_type} | "
                    f"cid={cid} | "
                    f"args={safe_args_summary} | "
                    f"success=False | "
                    f"duration={duration:.3f}s | "
                    f"error={type(e).__name__}: {str(e)[:100]}"
                )
                raise
        return wrapper
    return decorator


def _mask_sensitive_data(data: Any) -> Any:
    """Hassas verileri maskele (Recursive)"""
    sensitive_keys = {'password', 'token', 'api_key', 'secret', 'credit_card', 'sifre', 'auth'}
    
    if isinstance(data, dict):
        return {
            k: _mask_sensitive_data(v) if not any(s in k.lower() for s in sensitive_keys) 
            else "***MASKED***" 
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [_mask_sensitive_data(i) for i in data]
    return data


def _extract_id(result: Any) -> Optional[str]:
    """Sonuçtan ID çıkar"""
    if isinstance(result, int):
        return str(result)
    if isinstance(result, dict) and 'id' in result:
        return str(result['id'])
    if hasattr(result, 'id'):
        return str(result.id)
    return None
