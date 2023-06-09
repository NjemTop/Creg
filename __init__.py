from __future__ import absolute_import, unicode_literals

# Этот код позволяет запустить Celery при старте Django
from crag.celery import app as celery_app

__all__ = ('celery_app',)
