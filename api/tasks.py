from celery import shared_task
from api.update_module import update_module_info
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
def add(x, y):
    return x + y
