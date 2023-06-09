from celery import shared_task
from api.update_module import update_module_info
from datetime import datetime
from django.utils import timezone
from main.models import ReportTicket
import requests
import json
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_module_info_task():
    try:
        update_module_info()
    except Exception as error_message:
        print('Ошибка: %s' % str(error_message))
        logger.error(f"Ошибка при запуске задачи: {error_message}")


@shared_task
def update_tickets():
    url = "https://boardmaps.happyfox.com/api/1.1/json/tickets/"
    auth = ('45357d176a5f4e25b740aebae58f189c','3b9e5c6cc6f34802ad5ae82bafdab3bd')
    headers = {'Content-Type': 'application/json'}
    
    # Calculate start_date and end_date
    today = datetime.now().date()
    start_date = today
    end_date = today
    
    params = {
        'q': f'last-staff-replied-on-or-after:"{start_date}" last-staff-replied-on-or-before:"{end_date}"',
        'page': 1,
        'size': 50
    }
    
    res = requests.get(url, auth=auth, headers=headers, params=params)
    if res.status_code != 200:
        print(f'Response status code: {res.status_code}')
        return
    res_json = res.json()

    for ticket_data in res_json.get('data', []):
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

        # Find existing ticket or create new one
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
            print(f'Created new ticket {ticket_id}')
        else:
            print(f'Updated ticket {ticket_id}')
