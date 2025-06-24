"""

Утилита для логирования ошибок в сервисах рассылки.
Предоставляет декоратор `log_errors`, который перехватывает исключения,
логирует их в Python-логгер, сохраняет в базу (MailingLog) и отправляет в WebSocket.
"""
from functools import wraps
import logging
from apps.mailings.logging_utils import send_ws_event, log_event

def log_errors(logger=None, extra_info=None):
    """
    Декоратор для перехвата и логирования исключений, возникших в методах/функциях.

    Args:
        logger (logging.Logger, optional): Явно переданный логгер. Если не указан — используется error_logger или logger у объекта.
        extra_info (callable, optional): Функция, формирующая более подробное сообщение об ошибке (например, из исключения).

    Returns:
        function: Обёрнутая функция, которая логирует ошибки в логгер, MailingLog и WebSocket.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as exc:
                # Выбираем логгер
                log_obj = (
                    logger
                    or (getattr(args[0], "error_logger", None) if args else None)
                    or (getattr(args[0], "logger", None) if args else None)
                    or logging.getLogger(func.__module__)
                )

                # По умолчанию просто str(exception), но можно переопределить через extra_info
                message = str(exc)
                if callable(extra_info):
                    try:
                        message = extra_info(*args, **kwargs, error=exc)
                    except Exception:
                        pass

                # Пишем в python-логгер
                log_obj.error(message)

                # Если объект (обычно self) содержит mailing_id — используем его для логирования в DB/WS
                mailing_id = getattr(args[0], "mailing_id", None)
                if mailing_id:
                    log_event(mailing_id, "error", message)
                    send_ws_event(mailing_id, "error", {"message": message})

                raise

        return wrapper
    return decorator
