from requests.exceptions import RequestException, HTTPError
from scripts.email.email_send import EmailService
from main.models import ContactsCard
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

def get_user_from_ticket_system(session, email):
    """
    Получает данные пользователя из тикет системы по электронной почте.

    Args:
        session (requests.Session): Сессия, используемая для запросов.
        email (str): Электронная почта пользователя, по которой ведется поиск.

    Returns:
        dict: Словарь с данными пользователя или None, если пользователь не найден.
    """
    try:
        response = session.get(f'{API_URL}/users/', params={"search": email})
        response.raise_for_status()
        response_data = response.json()
        if response_data['data']:
            # Возвращаем данные первого найденного пользователя
            return response_data['data'][0]
        scripts_info_logger.info(f"Пользователь электронной почты {email} не найден в тикет системе.")
        return None
    except HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP: {http_err}; Ответ: {response.content}")
    except RequestException as req_err:
        scripts_error_logger.error(f"Ошибка запроса: {req_err}")
    except Exception as exc:
        scripts_error_logger.error(f"Общая ошибка: {exc}")
        scripts_error_logger.error(traceback.format_exc())


def update_ticket_system_user(session, user_id, contact):
    """
    Обновляет данные пользователя в тикет системе.

    Args:
        session (requests.Session): Сессия, используемая для запросов.
        user_id (int): Уникальный идентификатор пользователя в тикет системе.
        contact (dict): Словарь с данными контакта, которые нужно обновить.

    Returns:
        None
    """
    data = {
        "name": contact['firstname'] if contact['firstname'] else "Имя не указано",
        "lastname": contact['lastname'] if contact['lastname'] else "Фамилия не указана",
        "email": contact['contact_email'],
        "phone": contact['contact_number'],
    }
    try:
        response = session.put(
            f"{API_URL}/users/{user_id}",
            json=data
        )
        response.raise_for_status()  # Убедимся, что запрос успешен
        scripts_info_logger.info(f"Пользователь {contact['contact_email']} успешно обновлен в тикет системе")
    except HTTPError as http_err:
        if response.status_code == 400:
            # Попробуем обработать ошибку, связанную с некорректными данными имени
            error_details = response.json()
            errors = error_details.get('errors', [])
            for error in errors:
                if "Field {name} is incorrect or empty" in error.get('details', ''):
                    scripts_error_logger.info(f"Попытка исправления ошибки с именем для пользователя {contact['contact_email']}")
                    # Устанавливаем имя и фамилию на основе email
                    corrected_data = data.copy()
                    corrected_data["name"] = "CorrectedName"
                    corrected_data["lastname"] = "CorrectedLastName"
                    # Повторный запрос с исправленными данными
                    retry_response = session.put(f"{API_URL}/users/{user_id}", json=corrected_data)
                    retry_response.raise_for_status()
                    scripts_info_logger.info(f"Пользователь {contact['contact_email']} успешно обновлен после коррекции")
                    return
        # Если ошибка не из-за имени или не удалось исправить, логируем как ошибку
        scripts_error_logger.error(f"Ошибка HTTP: {http_err}; Ответ: {response.text}")
    except RequestException as req_err:
        scripts_error_logger.error(f"Ошибка запроса: {req_err}")
    except Exception as exc:
        scripts_error_logger.error(f"Общая ошибка: {exc}")
        scripts_error_logger.error(traceback.format_exc())


def create_user_in_ticket_system(session, contact, client_status, org_id=None):
    """
    Создает нового пользователя в тикет системе.

    Args:
        session (requests.Session): Сессия, используемая для запросов.
        contact (Union[ContactsCard, dict]): Объект контакта или словарь с информацией о новом пользователе.
        client_status (bool): Статус клиента для проверки перед созданием пользователя.
        org_id (int, optional): ID организации для привязки пользователя.
    """
    if isinstance(contact, ContactsCard):
        contact_dict = {
            'firstname': contact.firstname,
            'lastname': contact.lastname,
            'contact_email': contact.contact_email,
            'contact_number': contact.contact_number,
            'client_card__client_info__contact_status': contact.client_card.client_info.contact_status,
        }
    else:
        contact_dict = contact

    if not client_status:
        scripts_info_logger.info(f"Пропущено создание пользователя для {contact_dict['contact_email']} потому что клиент неактивен.")
        return

    password = "9ZYomj2oq1"  # Дефолтный пароль
    data = {
        "name": contact_dict['firstname'] if contact_dict['firstname'] else "Имя не указано",
        "lastname": contact_dict['lastname'] if contact_dict['lastname'] else "Фамилия не указана",
        "email": contact_dict['contact_email'],
        "phone": contact_dict['contact_number'],
        "group_id": 1,  # Устанавливаем группу пользователя "Клиент"
        "department": {  # Устанавливаем доступные департаменты клиенту. В данном случае ТП (1) и ПМО (5).
            "0": "1",
            "1": "5"
        },
        "password": password,
    }

    if org_id:
        data["organiz_id"] = org_id

    try:
        response = session.post(f"{API_URL}/users/", json=data)
        response.raise_for_status()
        scripts_info_logger.info(f"Новый пользователь {contact_dict['contact_email']} успешно создан в тикет системе")
        email_service = EmailService()
        # Отправка приветственного письма новому пользователю
        email_service.send_welcome_email(contact_dict, password)
    except HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP при создании пользователя: {http_err}; Ответ: {response.text}")
    except RequestException as req_err:
        scripts_error_logger.error(f"Ошибка запроса при создании пользователя: {req_err}")
    except Exception as exc:
        scripts_error_logger.error(f"Общая ошибка при создании пользователя: {exc}")
        scripts_error_logger.error(traceback.format_exc())


def update_user_status(session, user_id, status):
    """
    Обновляет статус пользователя в HDE.
    Args:
        session (requests.Session): Сессия, используемая для запросов.
        user_id (int): ID пользователя в системе.
        status (str): Новый статус пользователя ('active', 'inactive', 'disabled', 'fired').
    """
    url = f"{API_URL}/users/{user_id}"
    data = {"status": status}
    try:
        response = session.put(url, json=data)
        response.raise_for_status()
        scripts_info_logger.info(f"Статус пользователя {user_id} успешно обновлен на '{status}'.")
    except requests.HTTPError as http_err:
        scripts_error_logger.error(f"Ошибка HTTP при обновлении статуса пользователя {user_id}: {http_err}; Ответ: {response.text}")
    except Exception as err:
        scripts_error_logger.error(f"Ошибка при обновлении статуса пользователя {user_id}: {err}")
