from celery import shared_task
from .update_module import update_module_info

@shared_task
def update_module_info_task():
    update_module_info()
