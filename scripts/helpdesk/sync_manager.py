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

def update_organization_manager(session, org_id, manager):
    """
    Обновляет информацию о менеджере в тикет-системе.

    Args:
        session (requests.Session): Сессия, используемая для запросов.
        org_id (int): Идентификатор организации в тикет-системе.
        manager (UsersBoardMaps): Объект менеджера, информацию о котором нужно обновить.
    """
    data = {
        "custom_fields": {
            "8": manager.name
        }
    }
    try:
        response = session.put(f"{API_URL}/organizations/{org_id}", json=data)
        response.raise_for_status()
        scripts_info_logger.info(f"Информация о менеджере '{manager.name}' для организации {org_id} успешно обновлена.")
    except HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP при обновлении информации о менеджере '{manager.name}': {http_err}; Ответ: {response.text}")
    except RequestException as req_err:
        scripts_error_logger.error(f"Ошибка запроса при обновлении информации о менеджере '{manager.name}': {req_err}")
    except Exception as exc:
        scripts_error_logger.error(f"Общая ошибка при обновлении информации о менеджере '{manager.name}': {exc}")
        scripts_error_logger.error(traceback.format_exc())
