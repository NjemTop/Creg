from celery import shared_task
from api.update_module import update_module_info
from django.utils import timezone
from scripts.add_user_JFrog import authenticate, create_user
from scripts.update_tickets import update_tickets
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_module_info_task():
    try:
        update_module_info()
    except Exception as error_message:
        print('Ошибка: %s' % str(error_message))
        logger.error(f"Ошибка при запуске задачи: {error_message}")


@shared_task
def add_user_jfrog_task(username, password):
    try:
        # Вызов функций авторизации
        cookies = authenticate()
        if cookies:
            status_code = create_user(username, password, cookies)
            if status_code:
                print(f"Пользователь успешно создан. Код ответа: {status_code}")
                logger.info(f"Пользователь успешно создан. Код ответа: {status_code}")
            else:
                print("Ошибка при создании пользователя")
                logger.error("Ошибка при создании пользователя")
        else:
            print("Ошибка авторизации")
            logger.error("Ошибка авторизации")
    except Exception as error_message:
        logger.error(f"Ошибка при выполнении задачи: {error_message}")


@shared_task
def update_tickets_task():
    try:
        update_tickets()
    except Exception as error_message:
        print('Ошибка: %s' % str(error_message))
        logger.error(f"Ошибка при запуске задачи: {error_message}")