import requests
import json
from datetime import datetime
from main.models import ReportTicket
import logging

logger = logging.getLogger(__name__)


def update_tickets():
    """Функция для обновления тикетов"""
    try:
        # Настройки для запроса к API
        url = "https://boardmaps.happyfox.com/api/1.1/json/tickets/"
        auth = ('','')
        headers = {'Content-Type': 'application/json'}
        
        # Получение текущей даты
        today = datetime.now().date()
        start_date = today
        end_date = today
        
        # Параметры запроса к API
        params = {
            'q': f'last-staff-replied-on-or-after:"{start_date}" last-staff-replied-on-or-before:"{end_date}"',
            'page': 1,
            'size': 50
        }
        
        # Выполнение запроса к API
        res = requests.get(url, auth=auth, headers=headers, params=params)
        if res.status_code != 200:
            logger.error(f'Response status code: {res.status_code}')
            return
        
        # Обработка JSON-ответа от API
        res_json = res.json()
        process_tickets(res_json.get('data', []))
        
    except Exception as error_message:
        logger.error(f'Ошибка при выполнении задачи: {error_message}')


def process_tickets(ticket_data_list):
    """Функция для обработки списка тикетов"""
    for ticket_data in ticket_data_list:
        try:
            update_single_ticket(ticket_data)
        except Exception as error_message:
            logger.error(f'Ошибка при обработке тикета: {error_message}')


def update_single_ticket(ticket_data):
    """Функция для обновления одного тикета"""
    try:
        ticket_id = ticket_data['id']
        status = ticket_data['status']['name']
        subject = ticket_data['subject']
        creation_date = datetime.strptime(ticket_data['created_at'], '%Y-%m-%d %H:%M:%S').date()
        client_name = ticket_data['user']['name']
        priority = ticket_data['priority']['name']
        assignee_name = ticket_data['assigned_to']['name'] if ticket_data['assigned_to'] else ''
        updated_at = datetime.strptime(ticket_data['last_updated_at'], '%Y-%m-%d %H:%M:%S').date()
        last_reply_at = datetime.strptime(ticket_data['last_user_reply_at'], '%Y-%m-%d %H:%M:%S').date() if ticket_data['last_user_reply_at'] else None
        sla = ticket_data['sla_breaches'] > 0
        sla_time = ticket_data['sla_breaches']
        response_time = ticket_data['time_spent']
        cause = ''  # need to map from ticket_data
        module_boardmaps = ''  # need to map from ticket_data
        staff_message = ticket_data['messages_count']

        # Отправляем данные в таблицу для сохранения изменений о тикете
        ticket, created = ReportTicket.objects.update_or_create(
            ticket_id=ticket_id,
            defaults={
                'report_date': today,
                'status': status,
                'subject': subject,
                'creation_date': creation_date,
                'client_name': client_name,
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
        logger.error(f'Произошла ошибка при обновлении тикета: {error_message}')
