import logging
from functools import wraps

"""Utility decorator used in the mailing service.
In the original project it performed automatic retries and logging.
This simplified version only logs exceptions and re-raises them."""

def log_errors(logger=None, extra_info=None):
    """Decorator for logging exceptions inside mailing helpers."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # pragma: no cover - simple logging wrapper
                log = logger or logging.getLogger(func.__module__)
                message = str(exc)
                if callable(extra_info):
                    try:
                        message = extra_info(*args, **kwargs, error=exc)
                    except Exception:  # safety
                        pass
                log.error(message)
                raise
        return wrapper
    return decorator
