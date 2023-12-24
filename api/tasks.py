from celery import shared_task
from scripts.update_module import update_module_info
from django.utils import timezone
from scripts.add_user_JFrog import authenticate, create_user
from scripts.update_tickets import update_tickets
from scripts.artifactory_downloads_log.monitor_log import analyze_logs_and_update_db
from datetime import datetime
import logging
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts', get_abs_log_path('scripts_info.log'), logging.INFO)


@shared_task
def update_module_info_task():
    try:
        scripts_info_logger.info(f"Запуск задачи по обновлению модулей")
        update_module_info()
    except Exception as error_message:
        print('Ошибка: %s' % str(error_message))
        scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")


@shared_task
def add_user_jfrog_task(username, password):
    try:
        # Вызов функций авторизации
        cookies = authenticate()
        if cookies:
            status_code = create_user(username, password, cookies)
            if status_code:
                print(f"Пользователь успешно создан. Код ответа: {status_code}")
                scripts_info_logger.info(f"Пользователь успешно создан. Код ответа: {status_code}")
            else:
                print("Ошибка при создании пользователя")
                scripts_error_logger.error("Ошибка при создании пользователя")
        else:
            print("Ошибка авторизации")
            scripts_error_logger.error("Ошибка авторизации")
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при выполнении задачи: {error_message}")


@shared_task
def update_tickets_task():
    try:
        # Получение текущей даты
        today = datetime.now().date()
        start_date = today
        end_date = today
        scripts_info_logger.info(f"Запуск задачи по обновлению тикетов")
        update_tickets(start_date, end_date)
    except Exception as error_message:
        print('Ошибка: %s' % str(error_message))
        scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")


@shared_task
def artifactory_downloads_log_task():
    try:
        scripts_info_logger.info(f"Запуск задачи по обновлению информации о скачивании в jFrog")
        analyze_logs_and_update_db()
    except Exception as error_message:
        print('Ошибка: %s' % str(error_message))
        scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")
