from django.conf import settings
import os
from dotenv import load_dotenv

load_dotenv()


def set_email_config(env='prod'):
    if env == 'prod':
        settings.EMAIL_HOST = os.environ.get('EMAIL_HOST_PROD')
        settings.EMAIL_PORT = int(os.environ.get('EMAIL_PORT_PROD'))
        settings.EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER_PROD')
        settings.EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD_PROD')
        settings.DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL_PROD')
    elif env == 'internal':
        settings.EMAIL_HOST = os.environ.get('EMAIL_HOST_INTERNAL')
        settings.EMAIL_PORT = int(os.environ.get('EMAIL_PORT_INTERNAL'))
        settings.EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER_INTERNAL')
        settings.EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD_INTERNAL')
        settings.DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL_INTERNAL')
