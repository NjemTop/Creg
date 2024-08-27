from requests.exceptions import RequestException, HTTPError
import os
from dotenv import load_dotenv
import logging
import traceback
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

load_dotenv()

# Настройки для запроса к API
API_URL = os.environ.get('API_URL_TICKETS')


def find_organization_id(session, client_name):
    """
    Находит идентификатор организации в тикет системе по имени клиента.
    Args:
        session (requests.Session): Сессия, используемая для запросов.
        client_name (str): Имя клиента, по которой ведется поиск.

    Returns:
        dict: Словарь с данными компании или None, если компания не найдена.
    """
    try:
        response = session.get(f"{API_URL}/organizations/", params={"search": client_name})
        response.raise_for_status()
        data = response.json()
        if data.get('data'):
            return data['data'][0]['id']
        return None
    except HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP: {http_err}; Ответ: {response.content}")
    except RequestException as req_err:
        scripts_error_logger.error(f"Ошибка запроса: {req_err}")
    except Exception as exc:
        scripts_error_logger.error(f"Общая ошибка: {exc}")
        scripts_error_logger.error(traceback.format_exc())

def update_organization_version(session, org_id, server_version):
    """
    Обновляет информацию о версии сервера в тикет-системе.

    Args:
        session (requests.Session): Сессия, используемая для запросов.
        org_id (int): Идентификатор организации в тикет-системе.
        server_version (str): Строка с версией сервера для обновления.
    """
    data = {
        "custom_fields": {
            "7": server_version
        }
    }
    try:
        response = session.put(f"{API_URL}/organizations/{org_id}", json=data)
        response.raise_for_status()
        scripts_info_logger.info(f"Информация о версии сервера для организации {org_id} успешно обновлена.")
    except HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP при обновлении информации о версии сервера: {http_err}; Ответ: {response.text}")
    except RequestException as req_err:
        scripts_error_logger.error(f"Ошибка запроса при обновлении информации о версии сервера: {req_err}")
    except Exception as exc:
        scripts_error_logger.error(f"Общая ошибка при обновлении информации о версии сервера: {exc}")
        scripts_error_logger.error(traceback.format_exc())
