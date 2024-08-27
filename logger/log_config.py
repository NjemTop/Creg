import logging
import traceback
from logging.handlers import RotatingFileHandler
from functools import wraps
import graypy
import os

def get_abs_log_path(log_filename):
    # Получаем абсолютный путь до файла с настройками логгера (log_config.py)
    log_config_path = os.path.abspath(os.path.dirname(__file__))
    # Получаем абсолютный путь до корневой папки проекта
    project_root = os.path.dirname(log_config_path)
    # Формируем абсолютный путь до папки logs и файла с логами
    log_file_path = os.path.join(project_root, 'logs', log_filename)
    return log_file_path

def setup_logger(logger_name, log_file, level=logging.INFO, max_size=10, backup_count=10, encoding='utf-8'):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    try:
        # Создаем папку logs, если её еще нет
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        # logging.info(f"Directory {os.path.dirname(log_file)} created successfully.")

        # Создаем файл с логами, если еще не существует
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                pass
            logging.info(f"Log file {log_file} created successfully.")
        
        handler = RotatingFileHandler(log_file, maxBytes=max_size*1024*1024, backupCount=backup_count, encoding=encoding)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M')
        handler.setFormatter(formatter)

        # Удаляем все обработчики, если они уже есть, и добавляем новый
        logger.handlers = []
        logger.addHandler(handler)

        # Добавляем обработчик для отправки логов в Graylog через GELF
        graylog_handler = graypy.GELFTCPHandler('IT-GLOG-MON01P.corp.boardmaps.com', port=12201)
        graylog_handler.facility = 'scripts'
        logger.addHandler(graylog_handler)

        # logging.info(f"Logger {logger_name} setup successfully.")

    except Exception as e:
        logging.error(f"Error setting up logger {logger_name}: {e}")
    
    return logger

scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)

def log_errors(log_level=logging.ERROR, log_traceback=True, exception_types=(Exception,), extra_info=None):
    """
    Декоратор для логирования ошибок в функциях.

    Args:
        log_level (int): Уровень логирования (например, logging.ERROR, logging.WARNING).
        log_traceback (bool): Логировать трассировку стека ошибок.
        exception_types (tuple): Типы исключений, которые нужно логировать.
        extra_info (callable): Функция, возвращающая дополнительную информацию для логов.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = scripts_error_logger
            try:
                return func(*args, **kwargs)
            except exception_types as error:
                
                # Логируем основное сообщение об ошибке
                logger.log(log_level, f"Ошибка в {func.__name__}: {str(error)}")
                
                # Логируем дополнительную информацию, если она указана
                if extra_info:
                    extra = extra_info(*args, **kwargs)
                    logger.log(log_level, f"Дополнительная информация: {extra}")
                
                # Логируем трассировку стека, если это необходимо
                if log_traceback:
                    traceback_str = traceback.format_exc()
                    logger.log(log_level, f"Трассировка стека: {traceback_str}")
                
                # Повторно выбрасываем исключение
                raise
        return wrapper
    return decorator
