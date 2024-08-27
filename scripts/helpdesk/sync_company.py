import requests
import os
from logger.log_config import setup_logger, get_abs_log_path
import logging

# Настройки логирования
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), level=logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), level=logging.INFO)

# Настройки для запроса к API
API_URL = os.environ.get('API_URL_TICKETS')

def update_organization_status(session, org_id, is_active):
    """
    Обновляет статус активности организации в HDE.
    Args:
        session (requests.Session): Сессия, используемая для запросов.
        org_id (int): Идентификатор организации в HDE.
        is_active (bool): Статус активности организации (True если активна, False если неактивна).
    Returns:
        tuple: (bool, dict) - Первый элемент True если обновление прошло успешно, иначе False.
                               Второй элемент содержит ответ от сервера в форме словаря, если запрос успешен, иначе None.
    """
    url = f"{API_URL}/organizations/{org_id}"
    status_value = "1" if is_active else "0"
    data = {"custom_fields": {"4": status_value}}

    try:
        response = session.put(url, json=data)
        response.raise_for_status()
        response_data = response.json()
        scripts_info_logger.info(f"Статус организации с ID {org_id} успешно обновлен на {'активный' if is_active else 'неактивный'}.")
        return True, response_data
    except requests.HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP при обновлении статуса организации: {http_err}; Ответ: {response.text}")
        return False, None
    except Exception as err:
        scripts_error_logger.error(f"Ошибка при обновлении статуса организации: {err}")
        return False, None
