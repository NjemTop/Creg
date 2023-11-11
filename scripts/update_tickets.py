import requests
import json
from main.models import ReportTicket
import logging
from datetime import datetime
import os
from dotenv import load_dotenv


load_dotenv()

# Глобальные константы
CAUSE_NAME = 'Причина возникновения'
BOARDMAPS_MODULE_NAME = 'Модуль BoardMaps'
DEFAULT_VALUE = "Не указан"
# Настройки для запроса к API
API_URL = os.environ.get('API_URL_TICKETS')
API_AUTH = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
HEADERS = {'Content-Type': 'application/json'}

logger = logging.getLogger(__name__)


def update_tickets(start_date, end_date):
    """Функция для обновления тикетов"""
    try:
        with requests.Session() as session:
            session.auth = API_AUTH
            session.headers.update(HEADERS)
            # Параметры запроса к API
            params = {
                'category': 1,
                'q': f'last-staff-replied-on-or-after:"{start_date}" last-staff-replied-on-or-before:"{end_date}"',
                'page': 1,
                'size': 50
            }
            
            # Выполнение запроса к API для первой страницы
            res = session.get(API_URL, params=params)
            if res.status_code != 200:
                logger.error(f'Код статуса ответа: {res.status_code}')
                return
            
            # Обработка JSON-ответа от API
            res_json = res.json()
            total_pages = res_json['page_info']['page_count']  # Общее количество страниц
            
            # Обработка тикетов для первой страницы
            process_tickets(res_json.get('data', []))
            
            # Перебор и обработка тикетов для оставшихся страниц
            for page in range(2, total_pages + 1):
                params['page'] = page
                res = session.get(API_URL, params=params)
                if res.status_code != 200:
                    logger.error(f'Код статуса ответа: {res.status_code} для страницы {page}')
                    continue
                
                res_json = res.json()
                process_tickets(res_json.get('data', []))
        
    except requests.RequestException as error_message:
        logger.error(f'Ошибка при выполнении запроса: {error_message}')
    except Exception as error_message:
        logger.error(f'Неизвестная ошибка: {error_message}')


def process_tickets(ticket_data_list):
    """Функция для обработки списка тикетов"""
    for ticket_data in ticket_data_list:
        try:
            update_single_ticket(ticket_data)
        except Exception as error_message:
            logger.error(f'Ошибка при обработке тикета: {error_message}')


def extract_cause(custom_fields):
    cause = DEFAULT_VALUE

    field_values = {field['name']: field.get('value', DEFAULT_VALUE) for field in custom_fields}

    if CAUSE_NAME in field_values:
        cause = field_values[CAUSE_NAME]
        
        if cause in field_values:
            nested_value = field_values[cause]
            if nested_value in field_values:
                cause = f"{nested_value}: {field_values[nested_value]}"
            elif nested_value and nested_value != "Другое":
                cause = nested_value
        elif cause == "Другое":
            cause = f"{cause}: {field_values.get('Комментарий  другое', DEFAULT_VALUE)}"

    elif 'Запрос на поддержку' in field_values and field_values['Запрос на поддержку'] == "Другое":
        cause = f"{field_values['Запрос на поддержку']}: {field_values.get('Комментарий к запросу', DEFAULT_VALUE)}"

    elif 'Инцидент' in field_values and field_values['Инцидент'] == "Другое":
        cause = f"{field_values['Инцидент']}: {field_values.get('Комментарий к инциденту', DEFAULT_VALUE)}"

    return cause

def update_single_ticket(ticket_data):
    """Функция для обновления одного тикета"""
    try:
        ticket_id = ticket_data['id']
        status = ticket_data['status']['name']
        subject = ticket_data['subject']
        creation_date = datetime.strptime(ticket_data['created_at'], '%Y-%m-%d %H:%M:%S').date()
        client_name = ticket_data['user']['contact_groups'][0]['name']
        initiator = ticket_data['user']['name']
        priority = ticket_data['priority']['name']
        assignee_name = ticket_data['assigned_to']['name'] if ticket_data['assigned_to'] else ''
        updated_at = datetime.strptime(ticket_data['last_updated_at'], '%Y-%m-%d %H:%M:%S').date()
        last_reply_at = datetime.strptime(ticket_data['last_user_reply_at'], '%Y-%m-%d %H:%M:%S').date() if ticket_data['last_user_reply_at'] else None
        sla = ticket_data['sla_breaches'] > 0
        sla_time = ticket_data['sla_breaches']
        response_time = ticket_data['time_spent']
        # Извлечение причины и модули
        cause = "Не указан"
        module_boardmaps = "Не указан"
        custom_fields = ticket_data['custom_fields']

        # Проходим по массиву custom_fields и ищем нужные значения
        for field in custom_fields:
            if field['name'] == 'Причина возникновения':
                cause = field['value'] if field['value'] else "Не указан"
                
                nested_value = None
                next_level_name = cause
                next_level_value = None

                # Проверяем наличие следующего уровня
                for nested_field in custom_fields:
                    if nested_field['name'] == cause:
                        nested_value = nested_field.get('value')
                        next_level_name = nested_value

                        # Проверяем наличие третьего уровня
                        for next_level_field in custom_fields:
                            if next_level_field['name'] == next_level_name:
                                next_level_value = next_level_field.get('value')
                                break

                        if next_level_value:
                            cause = f"{next_level_name}: {next_level_value}"
                        elif nested_value and nested_value != "Другое":
                            cause = nested_value

                        break

                # Если на первом уровне "Другое", ищем второй уровень
                if cause == "Другое":
                    for next_level_field in custom_fields:
                        if next_level_field['name'] == 'Комментарий  другое':
                            cause = f"{cause}: {next_level_field.get('value')}"
                            break

            elif field['name'] == 'Запрос на поддержку':
                support_request_value = field['value']
                
                # Если на втором уровне "Другое", ищем третий уровень
                if support_request_value == "Другое":
                    for next_level_field in custom_fields:
                        if next_level_field['name'] == 'Комментарий к запросу':
                            cause = f"{support_request_value}: {next_level_field.get('value')}"
                            break

            elif field['name'] == 'Инцидент':
                incident_value = field['value']

                # Если на втором уровне "Другое", ищем третий уровень
                if incident_value == "Другое":
                    for next_level_field in custom_fields:
                        if next_level_field['name'] == 'Комментарий к инциденту':
                            cause = f"{incident_value}: {next_level_field.get('value')}"
                            break

            elif field['name'] == 'Модуль BoardMaps':
                module_boardmaps = field['value'] if field['value'] else "Не указан"

        staff_message = ticket_data['messages_count']

        # Получение текущей даты
        today = datetime.now().date()

        # Отправляем данные в таблицу для сохранения изменений о тикете
        ticket, created = ReportTicket.objects.update_or_create(
            ticket_id=ticket_id,
            defaults={
                'report_date': today,
                'status': status,
                'subject': subject,
                'creation_date': creation_date,
                'client_name': client_name,
                'initiator': initiator,
                'priority': priority,
                'assignee_name': assignee_name,
                'updated_at': updated_at,
                'last_reply_at': last_reply_at,
                'sla': sla,
                'sla_time': sla_time,
                'response_time': response_time,
                'cause': cause,
                'module_boardmaps': module_boardmaps,
                'staff_message': staff_message,
            }
        )
        
        if created:
            logger.info(f'Создан новый тикет {ticket_id}')
        else:
            logger.info(f'Обновленный тикет {ticket_id}')
            
    except KeyError as key_error:
        logger.error(f'Ошибка обработки ключа: {key_error}')
        
    except ValueError as value_error:
        logger.error(f'Ошибка преобразования значения: {value_error}')
        
    except Exception as error_message:
        logger.error(f'Произошла ошибка при обновлении тикета {ticket_id}. Ошибка: {error_message}')
