import requests
import json
import string
import random
import logging
from logger.log_config import setup_logger, get_abs_log_path
import os
from dotenv import load_dotenv


load_dotenv()


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


JFROG_USER = os.environ.get('JFROG_USER')
JFROG_PASSWORD = os.environ.get('JFROG_PASSWORD')
JFROG_URL = os.environ.get('JFROG_URL')

def authenticate():
    """
    Функция для авторизации в систему JFrog
    """
    # URL для авторизации
    url = f"{JFROG_URL}/api/v1/ui/auth/login?_spring_security_remember_me=false"

    # Заголовки для авторизации
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Данные для авторизации
    data = {
        "user": JFROG_USER,
        "password": JFROG_PASSWORD,
        "type": "login"
    }

    # Пробуем отправить POST-запрос
    try:
        response = requests.post(url, headers=headers, json=data)
        # Проверяем статус-код ответа 200, если нет, то выбросим в ошибку
        response.raise_for_status()
    except requests.exceptions.HTTPError as error_message:
        scripts_error_logger.error(f"HTTP запрос вернул ошибку: {error_message}")
        return None
    except requests.exceptions.ConnectionError as error_message:
        scripts_error_logger.error(f"Ошибка подключения: {error_message}")
        return None
    except requests.exceptions.Timeout as error_message:
        scripts_error_logger.error(f"Ошибка тайм-аута: {error_message}")
        return None
    except requests.exceptions.RequestException as error_message:
        scripts_error_logger.error(f"Общая ошибка: {error_message}")
        return None

    # Возвращаем cookies, полученные после авторизации
    return response.cookies


def create_user(username, password, cookies):
    """
    Функция для создания пользователя.
    На себя принимает "username" и "password",
    а также "cookies" полученные ранее при авторизации в систему JFrog
    """
    # URL для создания пользователя
    url = f"{JFROG_URL}/api/v1/access/api/ui/users"

    # Заголовки для создания пользователя
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Формируем данные для создания пользователя
    data = {
        "profileUpdatable": True,
        "internalPasswordDisabled": False,
        "watchManager": False,
        "reportsManager": False,
        "policyManager": False,
        "resourcesManager": False,
        "policyViewer": False,
        "email": f"{username}@example.com",
        "password": password,
        "username": username,
        "groups": ["Clients"],
        "disableUiAccess": True
    }

    # Пробуем отправить POST-запрос для создания УЗ
    try:
        response = requests.post(url, headers=headers, json=data, cookies=cookies)
        # Проверяем статус-код ответа 200, если нет, то выбросим в ошибку
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        scripts_error_logger.error(f"HTTP запрос вернул ошибку: {errh}")
        return None
    except requests.exceptions.ConnectionError as errc:
        scripts_error_logger.error(f"Ошибка подключения: {errc}")
        return None
    except requests.exceptions.Timeout as errt:
        scripts_error_logger.error(f"Ошибка тайм-аута: {errt}")
        return None
    except requests.exceptions.RequestException as error_message:
        scripts_error_logger.error(f"Общая ошибка: {error_message}")
        return None

    # Возвращаем статус-код ответа
    return response.status_code

def generate_random_password():
    """
    Функция генерации случайного пароля
    """
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits

    password_characters = uppercase_letters + lowercase_letters + digits
    password_length = 10

    password = ''.join(random.choice(password_characters) for _ in range(password_length))
    return password


# # Вызов функций авторизации
# cookies = authenticate()

# if cookies:
#     status_code = create_user("test_user", "Rfnzkj123123", cookies)
#     if status_code:
#         print(f"Пользователь успешно создан. Код ответа: {status_code}")
#     else:
#         print("Ошибка при создании пользователя")
# else:
#     print("Ошибка авторизации")
