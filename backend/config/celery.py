import os
from celery import Celery
from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Название проекта в Celery можно давать любое, для удобства возьмём "creg".
app = Celery("creg")

# Здесь указываем URL для брокера (используем PostgreSQL через SQLAlchemy).
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST", default="localhost")
DB_PORT = config("DB_PORT", default="5432")
DB_NAME = config("DB_NAME")

# Формируем строку для SQLAlchemy (PostgreSQL):
CELERY_BROKER_URL = f"sqla+postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Устанавливаем конфигурацию Celery
app.conf.broker_url = CELERY_BROKER_URL
app.conf.result_backend = "django-db"  # для хранения результатов в БД (django-celery-results)

# Включаем модули для периодических задач
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

# Автоматический поиск и регистрация задач (tasks.py) в установленных приложениях Django
app.autodiscover_tasks()
