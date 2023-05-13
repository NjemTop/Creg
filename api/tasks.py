from celery import shared_task
from . import update_module

@shared_task
def update_module_info_task():
    update_module.update_module_info()
