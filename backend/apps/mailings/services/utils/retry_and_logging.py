import smtplib
import logging
from retrying import retry  # экспортируем, чтобы использовать в других модулях
from logger.log_config import scripts_error_logger


def log_errors(extra_info=None):
    """
    Декоратор для логирования ошибок в функции.

    Args:
        extra_info (callable): функция, возвращающая доп. текст по ошибке (опционально)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                extra = f" ({extra_info(error=e)})" if extra_info else ""
                scripts_error_logger.error(f"Ошибка в '{func.__name__}': {str(e)}{extra}")
                raise
        return wrapper
    return decorator


def send_email_extra_info(*args, **kwargs):
    """
    Возвращает понятное описание ошибок, связанных с EmailSender.
    """
    error = kwargs.get('error')
    if isinstance(error, FileNotFoundError):
        return f"Файл не найден: {error.filename}"
    elif isinstance(error, smtplib.SMTPException):
        return f"Ошибка при отправке письма через SMTP: {str(error)}"
    elif isinstance(error, ValueError):
        return f"Неверное значение: {str(error)}"
    elif isinstance(error, KeyError):
        return f"Ключ не найден: {str(error)}"
    return "Неизвестная ошибка при отправке письма"
