from __future__ import absolute_import
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crag.settings')

from django.conf import settings  # noqa

app = Celery('crag', broker='amqp://guest:guest@rabbitmq:5672//')
