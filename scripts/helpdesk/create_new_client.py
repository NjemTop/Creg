import requests
import os
from logger.log_config import setup_logger, get_abs_log_path
import logging

# Настройки логирования
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), level=logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), level=logging.INFO)

# Настройки для запроса к API
API_URL = os.environ.get('API_URL_TICKETS')

def create_organization_in_hde(session, name, server_version, manager_name, service_pack, domains):
    """
    Создает новую организацию в HDE.
    Args:
        session (requests.Session): Сессия, используемая для запросов.
        name (str): Название организации для создания.
        server_version (str): Версия сервера для организации.
        manager_name (str): Имя менеджера для организации.
        service_pack (str): Тарифный план для организации.
        domains (str): Домены организации через запятую.
    Returns:
        int: ID созданной организации, или None если произошла ошибка.
    """
    url = f"{API_URL}/organizations/"
    data = {
        "name": name,
        "custom_fields": {
            "8": manager_name,
            "4": 1,
            "7": server_version,
            "9": service_pack
        },
        "domains": domains
    }

    try:
        response = session.post(url, json=data)
        response.raise_for_status()
        org_data = response.json()
        org_id = org_data['data'].get('id')
        scripts_info_logger.info(f"Организация '{name}' успешно создана с ID {org_id}.")
        return org_id
    except requests.HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP при создании организации: {http_err}; Ответ: {response.text}")
    except Exception as err:
        scripts_error_logger.error(f"Ошибка при создании организации: {err}")
        scripts_error_logger.error(traceback.format_exc())

    return None

