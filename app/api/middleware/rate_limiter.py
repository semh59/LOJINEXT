"""
Rate limiter adapter.

If `slowapi` is not installed, expose a no-op limiter so module imports do not
break in lightweight test/dev environments.
"""

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ImportError:
    Limiter = None
    get_remote_address = None


class _NoopLimiter:
    def limit(self, *_args, **_kwargs):
        def _decorator(func):
            return func

        return _decorator


limiter = Limiter(key_func=get_remote_address) if Limiter else _NoopLimiter()
