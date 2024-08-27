from django.http import HttpResponse, JsonResponse, HttpResponseServerError, FileResponse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
import json
from datetime import datetime
import logging
import os
from django.conf import settings
import smtplib
import re
import requests
from collections import defaultdict
from main.models import ReportTicket
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, DateField
from django.db.models.functions import Trunc
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from main.models import (ClientsList, ClientsCard, ContactsCard, TechAccountCard, ConnectInfoCard, 
BMServersCard, ServiseCard, TechInformationCard, ConnectionInfo, TechNote, UsersBoardMaps)
from django.contrib.auth.hashers import make_password, check_password
from scripts.release.mailing import send_test_email, send_mailing
from scripts.helpdesk.report_generator import generate_report, send_report
from scripts.helpdesk.service_request import HelpDeskEddyClient
from scripts.email.email_send import EmailService


# Настройка логирования
logger = logging.getLogger(__name__)


def format_datetime(dt):
    if dt:
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    return None

def format_duration(duration):
    if duration:
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours}h {minutes}m {seconds}s'
    return None

def get_tickets(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        step = request.GET.get('step', 'month')
        support = request.GET.get('support', None)
        
        # Фильтруем тикеты по дате создания
        created_tickets = ReportTicket.objects.filter(creation_date__range=[start_date, end_date])
        closed_tickets = ReportTicket.objects.filter(closed_date__range=[start_date, end_date], status__in=["Closed", "Выполнено"])
        
        # Агрегация тикетов в зависимости от выбранного шага
        if step == 'day':
            created_agg = created_tickets.annotate(date=TruncDay('creation_date'))
            closed_agg = closed_tickets.annotate(date=TruncDay('closed_date'))
        elif step == 'week':
            created_agg = created_tickets.annotate(date=TruncWeek('creation_date'))
            closed_agg = closed_tickets.annotate(date=TruncWeek('closed_date'))
        elif step == 'month':
            created_agg = created_tickets.annotate(date=TruncMonth('creation_date'))
            closed_agg = closed_tickets.annotate(date=TruncMonth('closed_date'))
        elif step == 'year':
            created_agg = created_tickets.annotate(date=TruncYear('creation_date'))
            closed_agg = closed_tickets.annotate(date=TruncYear('closed_date'))
        
        created_agg = created_agg.values('date').annotate(created=Count('id')).order_by('date')
        closed_agg = closed_agg.values('date').annotate(closed=Count('id')).order_by('date')
        
        # Слияние данных по открытым и закрытым тикетам
        dates = set()
        data = defaultdict(lambda: {'created': 0, 'closed': 0})
        for ticket in created_agg:
            date_str = ticket['date'].strftime('%Y-%m-%d')
            data[date_str]['created'] = ticket['created']
            dates.add(date_str)
        for ticket in closed_agg:
            date_str = ticket['date'].strftime('%Y-%m-%d')
            data[date_str]['closed'] = ticket['closed']
            dates.add(date_str)

        dates = sorted(list(dates))
        created_counts = [data[date]['created'] for date in dates]
        closed_counts = [data[date]['closed'] for date in dates]
        
        detailed_data = list(created_tickets.values())
        for ticket in detailed_data:
            ticket['creation_date'] = format_datetime(ticket['creation_date'])
            ticket['closed_date'] = format_datetime(ticket['closed_date'])
            ticket['updated_at'] = format_datetime(ticket['updated_at'])
            ticket['last_reply_at'] = format_datetime(ticket['last_reply_at'])
            ticket['first_response_time'] = format_duration(ticket['first_response_time'])
            ticket['sla_time'] = format_duration(ticket['sla_time'])

        response_data = {
            'dates': dates,
            'created_counts': created_counts,
            'closed_counts': closed_counts,
            'data': detailed_data # Детальная информация по каждомой заявке
        }
        
        return JsonResponse(response_data, safe=False)
    except Exception as error_message:
        return HttpResponseServerError(f"Ошибка при получении данных: {str(error_message)}", status=400)

def opened_tickets(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        step = request.GET.get('step', 'day')
        support = request.GET.get('support', None)
        ci_filter = request.GET.get('ci', None)

        # Получаем все открытые тикеты
        open_tickets = ReportTicket.objects.exclude(status__in=["Closed", "Выполнено"])

        # Фильтр по дате, если заданы начальная и конечная даты
        if start_date and end_date:
            open_tickets = open_tickets.filter(creation_date__range=[start_date, end_date])

        # Получаем детальную информацию по открытым тикетам
        open_tickets_detail = open_tickets.values()

        if ci_filter and ci_filter.lower() == 'true':
            tickets = tickets.exclude(ci__isnull=True).exclude(ci='')

        # Агрегация данных по дате создания тикета
        daily_open_ticket_counts = open_tickets.annotate(date=TruncDay('creation_date', output_field=DateField())).values('date').annotate(count=Count('id')).order_by('date')

        response_data = {
            'open_tickets_count': open_tickets.count(),
            'tickets': list(open_tickets_detail),
            'daily_counts': list(daily_open_ticket_counts)
        }

        return JsonResponse(response_data, safe=False)
    except Exception as error_message:
        return HttpResponseServerError("Ошибка при получении данных:", str(error_message))

def closed_tickets(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        ci_filter = request.GET.get('ci', None)
        
        tickets = ReportTicket.objects.filter(closed_date__range=[start_date, end_date], status__in=["Closed", "Выполнено"])

        if ci_filter and ci_filter.lower() == 'true':
            tickets = tickets.exclude(ci__isnull=True).exclude(ci='')

        close_report_tickets = tickets.values()
        return JsonResponse(list(close_report_tickets), safe=False)
    except Exception as error_message:
        return HttpResponseServerError("Ошибка при получении данных:", str(error_message))


def closed_tickets_by_support(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        step = request.GET.get('step', 'month')
        support = request.GET.get('support', None)

        tickets = ReportTicket.objects.filter(closed_date__range=[start_date, end_date], status__in=["Closed", "Выполнено"])

        if support:
            tickets = tickets.filter(assignee_name=support, status__in=["Closed", "Выполнено"])

        if step == 'day':
            tickets = tickets.annotate(date=TruncDay('closed_date'))
        elif step == 'week':
            tickets = tickets.annotate(date=TruncWeek('closed_date'))
        elif step == 'month':
            tickets = tickets.annotate(date=TruncMonth('closed_date'))
        elif step == 'year':
            tickets = tickets.annotate(date=TruncYear('closed_date'))

        tickets = tickets.values('date', 'assignee_name').order_by('date').annotate(count=Count('id'))

        support_data = defaultdict(lambda: defaultdict(int))
        dates = set()

        for ticket in tickets:
            date_str = ticket['date'].strftime('%Y-%m-%d')
            assignee = ticket['assignee_name']
            count = ticket['count']
            support_data[assignee][date_str] += count
            dates.add(date_str)

        dates = sorted(list(dates))
        formatted_data = {'dates': dates, 'supportData': {}}

        for assignee, data in support_data.items():
            formatted_data['supportData'][assignee] = [data.get(date, 0) for date in dates]

        return JsonResponse(formatted_data, safe=False)
    except Exception as error_message:
        return HttpResponseServerError("Ошибка при получении данных:", str(error_message), status=400)


@csrf_exempt
@require_http_methods(["POST"])
def send_test_mailing(request):
    try:
        data = json.loads(request.body)
        server_version = data.get('server_version')
        email_send = data.get('email')
        ipad_version = data.get('ipad_version', None)
        android_version = data.get('android_version', None)
        mailing_type = data.get('mailing_type')  # Получаем тип рассылки из запроса
        release_type = data.get('release_type') # Параметр для типа релиза
        language = data.get('language')

        if send_test_email(email_send, mailing_type, release_type, server_version, ipad_version, android_version, language):
            return JsonResponse({'message': 'Тестовое письмо успешно отправлено.'}, status=200)
        else:
            return JsonResponse({'error': 'Ошибка при отправке письма'}, status=500)
    except json.JSONDecodeError as error_message:
        logger.error(f"Некорректный JSON: {error_message}")
        return JsonResponse({'error': 'Некорректный JSON: ' + str(error_message)}, status=400)
    except FileNotFoundError as error_message:
        logger.error(f"Файл не найден: {error_message}")
        return JsonResponse({'error': str(error_message)}, status=404)
    except smtplib.SMTPException as error_message:
        logger.error(f"Ошибка SMTP: {error_message}")
        return JsonResponse({'error': str(error_message)}, status=500)
    except requests.exceptions.RequestException as error_message:
        logger.error(f"Ошибка связи с Яндекс.Диском: {error_message}")
        return JsonResponse({'error': f"Ошибка связи с Яндекс.Диском: {str(error_message)}"}, status=500)
    except Exception as error_message:
        logger.error(f"Общая ошибка: {error_message}")
        return JsonResponse({'error': str(error_message)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_prod_mailing(request):
    try:
        data = json.loads(request.body)
        server_version = data.get('server_version')
        ipad_version = data.get('ipad_version', None)  # Необязательный параметр
        android_version = data.get('android_version', None)  # Необязательный параметр
        mailing_type = data.get('mailing_type')  # Получаем тип рассылки из запроса
        release_type = data.get('release_type') # Параметр для типа релиза

        result_message = send_mailing(mailing_type, release_type, server_version, ipad_version, android_version)
        if 'Ошибка' in result_message:
            logger.error(result_message)
            return JsonResponse({'error': result_message}, status=500)
        elif 'Предупреждение' in result_message:
            logger.warning(result_message)
            return JsonResponse({'message': result_message}, status=207)  # 207 Multi-Status
        else:
            logger.info(result_message)
            return JsonResponse({'message': result_message}, status=200)
    except json.JSONDecodeError as error_message:
        logger.error(f"Некорректный JSON: {error_message}")
        return JsonResponse({'error': 'Некорректный JSON: ' + str(error_message)}, status=400)
    except FileNotFoundError as error_message:
        logger.error(f"Файл не найден: {error_message}")
        return JsonResponse({'error': str(error_message)}, status=404)
    except smtplib.SMTPException as error_message:
        logger.error(f"Ошибка SMTP: {error_message}")
        return JsonResponse({'error': str(error_message)}, status=500)
    except requests.exceptions.RequestException as error_message:
        logger.error(f"Ошибка связи с Яндекс.Диском: {error_message}")
        return JsonResponse({'error': f"Ошибка связи с Яндекс.Диском: {str(error_message)}"}, status=500)
    except Exception as error_message:
        logger.error(f"Общая ошибка: {error_message}")
        return JsonResponse({'error': str(error_message)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_service_request(request):
    data = json.loads(request.body)
    release_version = data.get('release_version')

    if not release_version:
        return JsonResponse({'success': False, 'error': 'Номер релиза не предоставлен.'})

    version_prefix = release_version.split('.')[0] + '.'  # Получаем '2.' или '3.'

    clients = ServiseCard.objects.filter(service_pack__in=['Gold', 'Platinum'])
    success = False
    company_contacts = {}
    helpdesk_client = HelpDeskEddyClient()

    for client in clients:
        client_info = client.client_card.client_info

        # Проверка на активность клиента и исключение SaaS клиентов
        if not client_info.contact_status or client_info.saas:
            continue

        # Проверка на соответствие версии сервера
        tech_info = TechInformationCard.objects.filter(client_card=client.client_card)
        if not tech_info.exists() or not tech_info.first().server_version.startswith(version_prefix):
            continue

        company_name = client.client_card.client_info.client_name
        contacts = ContactsCard.objects.filter(client_card=client.client_card, notification_update=True)

        if not contacts.exists():
            continue

        # Получаем первую почту как "Кому", остальные в "Копия"
        to_email = contacts.first().contact_email
        cc_emails = [contact.contact_email for contact in contacts[1:]]

        try:
            helpdesk_client.send_service_request(release_version, to_email, cc_emails)
            company_contacts[company_name] = {
                'to': to_email,
                'cc': cc_emails
            }
            success = True
        except Exception as error_message:
            logger.error(f"Ошибка при отправке запроса для компании {company_name} ({to_email}): {str(error_message)}")
            continue

    if company_contacts:
        return JsonResponse({'success': success, 'companies': company_contacts})
    else:
        return JsonResponse({'success': False, 'error': 'Не удалось отправить ни одного запроса.'})


@csrf_exempt
@require_http_methods(["POST"])
def add_client_and_card(request):
    try:
        data = json.loads(request.body)

        # Создаем запись в ClientsList
        client = ClientsList(
            client_name=data['client_name'],
            short_name=data.get('short_name'),
            password=data.get('password'),
            contact_status=data.get('contact_status', True),
            service=data.get('service'),
            technical_information=data.get('technical_information'),
            integration=data.get('integration'),
            documents=data.get('documents'),
            notes=data.get('notes', '')
        )
        client.save()

        # Создаем связанную запись в ClientsCard
        client_card = ClientsCard(
            client_info=client,
            contacts=data.get('contacts', generate_unique_id()),
            tech_notes=data.get('tech_notes', generate_unique_id()),
            connect_info=data.get('connect_info', generate_unique_id()),
            rdp=data.get('rdp', generate_unique_id()),
            tech_account=data.get('tech_account', generate_unique_id()),
            bm_servers=data.get('bm_servers', generate_unique_id())
        )
        client_card.save()

        return JsonResponse({'message': 'Клиент и карточка клиента успешно созданы'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def change_client_status(request, client_id, action):
    if request.method == 'PATCH':
        # Получаем клиента по ID
        try:
            client = ClientsList.objects.get(pk=client_id)
        except ClientsList.DoesNotExist:
            return JsonResponse({'error': 'Клиент не найден'}, status=404)

        # Меняем статус клиента
        if action == 'suspend':
            client.contact_status = False
        elif action == 'activate':
            client.contact_status = True

            # Получаем контакты клиента для включения в уведомление
            contacts_data = ContactsCard.objects.filter(client_card__client_info=client)

            # Отправляем уведомление о переводе на ТП
            email_service = EmailService()
            error_message = email_service.send_support_transition_email(client, contacts_data)
            if error_message:
                return JsonResponse({'message': 'Статус клиента обновлен, но произошла ошибка при отправке уведомления', 'error': error_message}, status=500)
        client.save()

        return JsonResponse({'message': 'Статус клиента успешно обновлен'}, status=200)
    else:
        return HttpResponseBadRequest('Неподдерживаемый метод запроса')


@csrf_exempt
@require_http_methods(["POST"])
def add_tech_account(request, client_id):
    """
    Функция для добавления технической учётной записи клиента.
    """
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        data = json.loads(request.body)
        tech_account = TechAccountCard(
            client_card=client_card,
            contact_info_disc=data.get('description'),
            contact_info_account=data.get('account'),
            contact_info_password=data.get('password'),
        )
        tech_account.save()
        return JsonResponse({'message': 'Техническая учетная запись успешно создана'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_tech_account(request, account_id):
    """
    Функция для обновления технической учётной записи клиента.
    """
    try:
        tech_account = TechAccountCard.objects.get(pk=account_id)
    except TechAccountCard.DoesNotExist:
        return JsonResponse({'error': 'Техническая учетная запись не найдена'}, status=404)

    try:
        data = json.loads(request.body)
        if 'description' in data:
            tech_account.contact_info_disc = data['description']
        if 'account' in data:
            tech_account.contact_info_account = data['account']
        if 'password' in data:
            tech_account.contact_info_password = data['password']
        tech_account.save()
        return JsonResponse({'message': 'Техническая учетная запись успешно обновлена'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_tech_account(request, account_id):
    try:
        tech_account = TechAccountCard.objects.get(pk=account_id)
        tech_account.delete()
        return JsonResponse({'message': 'Техническая учетная запись успешно удалена'}, status=200)
    except TechAccountCard.DoesNotExist:
        return JsonResponse({'error': 'Техническая учетная запись не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def add_connect_info(request, client_id):
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        data = json.loads(request.body)
        connect_info = ConnectInfoCard(
            client_card=client_card,
            contact_info_name=data.get('name'),
            contact_info_account=data.get('account'),
            contact_info_password=data.get('password'),
        )
        connect_info.save()
        return JsonResponse({'message': 'Информация о подключении успешно создана'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_connect_info(request, connect_info_id):
    try:
        connect_info = ConnectInfoCard.objects.get(pk=connect_info_id)
    except ConnectInfoCard.DoesNotExist:
        return JsonResponse({'error': 'Информация о подключении не найдена'}, status=404)

    try:
        data = json.loads(request.body)
        if 'name' in data:
            connect_info.contact_info_name = data['name']
        if 'account' in data:
            connect_info.contact_info_account = data['account']
        if 'password' in data:
            connect_info.contact_info_password = data['password']
        connect_info.save()
        return JsonResponse({'message': 'Информация о подключении успешно обновлена'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_connect_info(request, connect_info_id):
    try:
        connect_info = ConnectInfoCard.objects.get(pk=connect_info_id)
        connect_info.delete()
        return JsonResponse({'message': 'Информация о подключении успешно удалена'}, status=200)
    except ConnectInfoCard.DoesNotExist:
        return JsonResponse({'error': 'Информация о подключении не найдена'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def add_contact(request, client_id):
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        data = json.loads(request.body)
        contact_card = ContactsCard(
            client_card=client_card,
            firstname=data.get('firstname'),
            lastname=data.get('lastname'),
            contact_position=data.get('position'),
            contact_email=data.get('email'),
            contact_number=data.get('number'),
            notification_update=data.get('notification_update'),
            contact_notes=data.get('contact_notes'),
        )
        contact_card.save()
        return JsonResponse({'message': 'Контакт успешно добавлен'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_contact(request, contact_id):
    try:
        contact_card = ContactsCard.objects.get(pk=contact_id)
    except ContactsCard.DoesNotExist:
        return JsonResponse({'error': 'Контакт не найден'}, status=404)

    try:
        data = json.loads(request.body)
        if 'firstname' in data:
            contact_card.firstname = data['firstname']
        if 'lastname' in data:
            contact_card.lastname = data['lastname']
        if 'position' in data:
            contact_card.contact_position = data['position']
        if 'email' in data:
            contact_card.contact_email = data['email']
        if 'number' in data:
            contact_card.contact_number = re.sub(r"\D", "", data['number'])
        # Проверяем наличие и преобразуем строковые значения 'true'/'false' в булевы
        if 'notification_update' in data:
            notification_update_value = data['notification_update'].lower()
            if notification_update_value == 'true':
                contact_card.notification_update = True
            elif notification_update_value == 'false':
                contact_card.notification_update = False
            else:
                # Обработка некорректного значения
                return JsonResponse({'error': 'Некорректное значение для notification_update'}, status=400)
        contact_card.save()
        return JsonResponse({'message': 'Контакт успешно обновлен'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_contact(request, contact_id):
    try:
        contact = ContactsCard.objects.get(pk=contact_id)
        contact.delete()
        return JsonResponse({'message': 'Контакт успешно удален'}, status=200)
    except ContactsCard.DoesNotExist:
        return JsonResponse({'error': 'Контакт не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def add_bm_server(request, client_id):
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        data = json.loads(request.body)
        bm_server = BMServersCard(
            client_card=client_card,
            bm_servers_circuit=data.get('circuit'),
            bm_servers_servers_name=data.get('servers_name'),
            bm_servers_servers_adress=data.get('servers_adress'),
            bm_servers_operation_system=data.get('operation_system'),
            bm_servers_url=data.get('url'),
            bm_servers_role=data.get('role'),
        )
        bm_server.save()
        return JsonResponse({'message': 'Запись сервера успешно создана'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_bm_server(request, server_id):
    try:
        bm_server = BMServersCard.objects.get(pk=server_id)
    except BMServersCard.DoesNotExist:
        return JsonResponse({'error': 'Запись сервера не найдена'}, status=404)

    try:
        data = json.loads(request.body)
        if 'circuit' in data:
            bm_server.bm_servers_circuit = data['circuit']
        if 'servers_name' in data:
            bm_server.bm_servers_servers_name = data['servers_name']
        if 'servers_adress' in data:
            bm_server.bm_servers_servers_adress = data['servers_adress']
        if 'operation_system' in data:
            bm_server.bm_servers_operation_system = data['operation_system']
        if 'url' in data:
            bm_server.bm_servers_url = data['url']
        if 'role' in data:
            bm_server.bm_servers_role = data['role']
        # for field in ['bm_servers_circuit', 'bm_servers_servers_name', 'bm_servers_servers_adress', 'bm_servers_operation_system', 'bm_servers_url', 'bm_servers_role']:
        #     if field in data:
        #         setattr(bm_server, field, data[field])
        bm_server.save()
        return JsonResponse({'message': 'Запись сервера успешно обновлена'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def add_service_card(request, client_id):
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        data = json.loads(request.body)
        service_card = ServiseCard(
            client_card=client_card,
            service_pack=data.get('service_pack'),
            manager=data.get('manager'),
            loyal=data.get('loyal', '')
        )
        service_card.save()
        return JsonResponse({'message': 'Информация об обслуживании успешно добавлена'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_service_card(request, service_card_id):
    try:
        service_card = ServiseCard.objects.get(pk=service_card_id)
    except ServiseCard.DoesNotExist:
        return JsonResponse({'error': 'Информация об обслуживании не найдена'}, status=404)

    try:
        data = json.loads(request.body)
        if 'service_pack' in data:
            service_card.service_pack = data['service_pack']
        try:
            if 'manager' in data:
                # Пытаемся найти менеджера по имени. Предполагается, что имена уникальны.
                manager_name = data['manager']
                manager = UsersBoardMaps.objects.get(name=manager_name)
                # Если менеджер найден, присваиваем его экземпляр полю `manager`
                service_card.manager = manager
        except UsersBoardMaps.DoesNotExist:
            # Обрабатываем случай, когда менеджер с таким именем не найден.
            return JsonResponse({'error': f'Менеджер с именем {manager_name} не найден'}, status=404)
        if 'loyal' in data:
            service_card.loyal = data['loyal']
        service_card.save()
        return JsonResponse({'message': 'Информация об обслуживании успешно обновлена'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def add_tech_information(request, client_id):
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        data = json.loads(request.body)
        tech_information = TechInformationCard.objects.create(
            client_card=client_card,
            server_version=data['server_version'],
            update_date=datetime.strptime(data['update_date'], '%Y-%m-%d').date(),
            api=data.get('api', False),
            ipad=data.get('ipad', ''),
            android=data.get('android', ''),
            mdm=data.get('mdm', ''),
            localizable_web=data.get('localizable_web', False),
            localizable_ios=data.get('localizable_ios', False),
            skins_web=data.get('skins_web', False),
            skins_ios=data.get('skins_ios', False)
        )
        return JsonResponse({'message': 'Техническая информация успешно добавлена'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_tech_information(request, info_id):
    try:
        tech_info = TechInformationCard.objects.get(pk=info_id)
    except TechInformationCard.DoesNotExist:
        return JsonResponse({'error': 'Техническая информация не найдена'}, status=404)

    try:
        data = json.loads(request.body)
        if 'server_version' in data:
            tech_info.server_version = data['server_version']
        if 'update_date' in data:
            tech_info.update_date = datetime.strptime(data['update_date'], '%Y-%m-%d').date()
        for field in ['api', 'ipad', 'android', 'mdm', 'localizable_web', 'localizable_ios', 'skins_web', 'skins_ios']:
            if field in data:
                setattr(tech_info, field, data[field])
        tech_info.save()
        return JsonResponse({'message': 'Техническая информация успешно обновлена'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def add_connection_info(request, client_id):
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        connection_info = ConnectionInfo(
            client_card=client_card,
            file_path=request.FILES.get('file'),
            text=request.POST.get('text')
        )
        connection_info.save()
        return JsonResponse({'message': 'Информация о подключении успешно создана'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PATCH"])
def update_connection_info(request, connection_id):
    try:
        connection_info = ConnectionInfo.objects.get(pk=connection_id)
    except ConnectionInfo.DoesNotExist:
        return JsonResponse({'error': 'Информация о подключению не найдена'}, status=404)

    try:
        data = json.loads(request.body)
        if 'text' in data:
            connection_info.text = data['text']
        if 'file' in request.FILES:
            connection_info.file_path = request.FILES['file']
        connection_info.save()
        return JsonResponse({'message': 'Информация о подключению успешно обновлена'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def add_tech_note(request, client_id):
    try:
        client_card = ClientsCard.objects.get(client_info_id=client_id)
    except ClientsCard.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

    try:
        data = json.loads(request.body)
        tech_note = TechNote(
            client_card=client_card,
            tech_note_text=data.get('tech_note_text')
        )
        tech_note.save()
        return JsonResponse({'message': 'Техническая заметка успешно создана'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_tech_note(request, note_id):
    try:
        tech_note = TechNote.objects.get(pk=note_id)
    except TechNote.DoesNotExist:
        return JsonResponse({'error': 'Техническая заметка не найдена'}, status=404)

    try:
        data = json.loads(request.body)
        if 'tech_note_text' in data:
            tech_note.tech_note_text = data['tech_note_text']
        tech_note.save()
        return JsonResponse({'message': 'Техническая заметка успешно обновлена'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def upload_template(request):
    """
    Обработчик загрузки шаблонов на сервер 
    """
    if request.method == 'POST':
        file = request.FILES['file']
        template_name = request.POST.get('templateName')
        # Сохраните файл в соответствующую директорию
        with open(os.path.join(os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML'), template_name), 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return HttpResponse('Файл успешно загружен')
    return HttpResponse('Метод не поддерживается', status=405)

def download_template(request, template_name):
    """
    Обработчик скачивания выбранного шаблонов с сервера
    """
    file_path = os.path.join(os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML'), template_name)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    return HttpResponse('Файл не найден', status=404)

def get_template_content(request, template_name):
    """
    Обработчик получения содержимого HTML шаблона
    """
    file_path = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', template_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return HttpResponse(file.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('Шаблон не найден', status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_tickets(request):
    # Получение данных из тела запроса
    data = json.loads(request.body)
    client_name = data.get('client_name')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    recipient_email = data.get('email')

    # Сохраняем список отсутствующих полей для детализации ошибки
    missing_fields = []
    if not client_name:
        missing_fields.append('client_name')
    if not start_date_str:
        missing_fields.append('start_date')
    if not end_date_str:
        missing_fields.append('end_date')
    if not recipient_email:
        missing_fields.append('email')

    # Проверка входных данных
    if missing_fields:
        missing_fields_str = ", ".join(missing_fields)
        logger.error(f"Ошибка: отсутствие обязательных полей: {missing_fields_str}")
        return JsonResponse({"error": f"Необходимо заполнить следующие поля: {missing_fields_str}"}, status=400)

    # Присваиваем значения по умолчанию
    start_date = None
    end_date = None

    # Преобразование строковых дат в объекты datetime
    try:
        start_date = datetime.strptime(start_date_str, "%d.%m.%Y").date()
        end_date = datetime.strptime(end_date_str, "%d.%m.%Y").date()
        if start_date > end_date:
            return JsonResponse({"error": "Дата начала должна быть до даты окончания"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": "Неверный формат даты"}, status=400)
    
    # Фильтрация данных из БД
    try:
        tickets = ReportTicket.objects.filter(
            client_name=client_name,
            updated_at__range=[start_date, end_date]
        )
        if not tickets:
            return JsonResponse({"error": "Заявки не найдены"}, status=404)
    except Exception as e:
        logger.error(f"Ошибка при запросе к базе данных: {e}")
        return JsonResponse({"error": "Ошибка при запросе к базе данных"}, status=500)

    file_path = generate_report(tickets, client_name, start_date_str, end_date_str)
    if not file_path:
        return JsonResponse({'error': 'Не удалось создать отчет'}, status=500)

    if not send_report(recipient_email, file_path, client_name, start_date, end_date):
        return JsonResponse({'error': 'Не удалось отправить отчет на почту'}, status=500)

    return JsonResponse({'status': 'success', 'message': "Отчет был отправлен на почту: " + recipient_email})


def get_advanced_search(request):
    managers = list(UsersBoardMaps.objects.filter(position='Менеджер').values('id', 'name'))
    tariff_plans = list(ServiseCard.objects.values_list('service_pack', flat=True).distinct())
    return JsonResponse({
        'managers': managers,
        'tariff_plans': tariff_plans
    })
