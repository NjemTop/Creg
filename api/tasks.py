from celery import shared_task
from scripts.update_module import update_module_info
from django.utils import timezone
from datetime import datetime
import logging
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


@shared_task
def update_module_info_task():
    try:
        scripts_info_logger.info(f"Запуск задачи по обновлению модулей")
        update_module_info()
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")
