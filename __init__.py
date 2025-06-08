from __future__ import absolute_import, unicode_literals

# Этот код позволяет запустить Celery при старте Django
# Модуль с конфигурацией Celery находится в пакете ``crag``,
# поэтому импортируем ``app`` оттуда. Ранее импорт выполнялся
# из корневого модуля, где файла ``celery.py`` нет, что
# приводило к ``ModuleNotFoundError`` при импорте пакета
# ``Creg`` и запуске тестов.
try:
    # Модуль с конфигурацией Celery находится в пакете ``crag``.
    # Импортируем приложение Celery, если пакет доступен.
    from crag.celery import app as celery_app
except ModuleNotFoundError:
    # В тестовой среде или при минимальной установке модуль может
    # отсутствовать. В таком случае просто игнорируем ошибку, чтобы
    # импорт пакета ``Creg`` не завершался с исключением.
    celery_app = None

__all__ = ('celery_app',)
