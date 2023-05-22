"""
Django settings for crag project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from dotenv import load_dotenv
from pathlib import Path
import os
import graypy

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)9j28#qir23k@sx0eun@ew&&1%fwwgjz%+_2fb25vkd)$ze0kw'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Указываем разрешение с какого адреса можно запускать сервер
ALLOWED_HOSTS = ['*']

# Добавляем русские буквы
JSON_USE_UTF8 = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'main',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'api',
    # выключил проверку на HTTPS
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'JSON_INDENT': 4,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # выключил проверку на HTTPS
    'corsheaders.middleware.CorsMiddleware',
    'api.middleware.AppendSlashWithPOSTMiddleware',
    'api.middleware.ExceptionLoggingMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# выключил проверку на HTTPS
CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'crag.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.favicon',
            ],
        },
    },
]

WSGI_APPLICATION = 'crag.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Делаем переменное окружение для определения локального запуска проекта или в докере (production)
# Перед запуском нужно выполнить команду: export DJANGO_ENV=local
# Windows set DJANGO_ENV=local
# Для установки переменного окружения DJANGO_ENV
DJANGO_ENV = os.environ.get('DJANGO_ENV')

if DJANGO_ENV == 'local':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'database_1_test',
            'USER': 'sa',
            'PASSWORD': 'kJGnTXBT',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'database_1.db',
            'USER': 'sa',
            'PASSWORD': 'kJGnTXBT',
            'HOST': 'db',
            'PORT': '5432',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

CELERY_BROKER_URL = 'amqp://admin:BfDVBPsNSf@rabbitmq:5672//'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_RESULT_BACKEND = 'db+postgresql://sa:kJGnTXBT@db/database_1.db'

# Настройка, которая убирает слэш в конце "/"
# APPEND_SLASH = False

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {  # Создаем запись логов со временем
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': './logs/debug.log',
            'when': 'midnight',  # Устанавливаем создане нового файла логов на полночь
            'interval': 1,  # Устанавливаем создание файлов на каждый день свой
            'backupCount': 10,  # Устанавливаем количество лог файлов
            'formatter': 'verbose',  # Применяем форматтер
        },
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': './logs/info.log',
            'maxBytes': 1024*1024*10,  # Устанавливаем размер файла логов в 10 MB
            'backupCount': 10,  # Устанавливаем количество файлов логов в 10 файлов
            'formatter': 'verbose',  # Применяем форматтер
        },
        'warning_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': './logs/warning.log',
            'maxBytes': 1024*1024*10, # Устанавливаем размер файла логов в 10 MB
            'backupCount': 5, # Устанавливаем количество файлов логов в 10 файлов
            'formatter': 'verbose', # Применяем форматтер
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': './logs/error.log',
            'maxBytes': 1024*1024*10,  # Устанавливаем размер файла логов в 10 MB
            'backupCount': 3,  # Устанавливаем количество файлов логов в 3 файла
            'formatter': 'verbose',  # Применяем форматтер
        },
        'critical_file': {
            'level': 'CRITICAL',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': './logs/critical.log',
            'maxBytes': 1024*1024*10,  # Устанавливаем размер файла логов в 10 MB
            'backupCount': 3,  # Устанавливаем количество файлов логов в 3 файла
            'formatter': 'verbose',  # Применяем форматтер
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',  # Применяем форматтер
        },
        'gelf': {
        'level': 'INFO',
        'class': 'graypy.GELFTCPHandler',
        'host': 'mongo',
        'port': 12201,  # Порт Graylog GELF UDP input
    },
    },
    'root': {
        'handlers': ['file', 'console', 'gelf'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'info_file', 'warning_file', 'error_file', 'critical_file', 'console', 'gelf'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
