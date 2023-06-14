from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging
from celery.signals import after_setup_logger
from django.conf import settings
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crag.settings')

app = Celery('crag', broker=os.getenv('CELERY_BROKER_URL'))

# Используем настройки Django для конфигурации Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Установка backend для результатов задач в Celery
app.conf.result_backend = 'db+postgresql://sa:kJGnTXBT@db/database_2'

# Автоматическая загрузка задач из файла tasks.py каждого приложения
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    logger.handlers = []
    logging.config.dictConfig(settings.LOGGING)
