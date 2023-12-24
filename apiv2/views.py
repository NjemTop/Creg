from django.http import HttpResponse, JsonResponse, HttpResponseServerError, FileResponse
import json
from datetime import datetime
import logging
import os
from django.conf import settings
import smtplib
import requests
from main.models import ReportTicket
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from main.models import (ClientsList, ClientsCard, ContactsCard, TechAccountCard, ConnectInfoCard, 
BMServersCard, ServiseCard, TechInformationCard, ConnectionInfo, TechNote)
from django.contrib.auth.hashers import make_password, check_password
from scripts.release.test_automatic_email import send_test_email


# Настройка логирования
logger = logging.getLogger(__name__)


def creation_tickets(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        report_tickets = ReportTicket.objects.filter(creation_date__range=[start_date, end_date]).values()
        return JsonResponse(list(report_tickets), safe=False)
    except Exception as error_message:
        return HttpResponseServerError("Ошибка при получении данных:", str(error_message), status=400)

def open_tickets(request):
    try:
        open_report_tickets = ReportTicket.objects.exclude(status="Closed").values()
        return JsonResponse(list(open_report_tickets), safe=False)
    except Exception as error_message:
        return HttpResponseServerError("Ошибка при получении данных:", str(error_message))


@csrf_exempt
@require_http_methods(["POST"])
def send_test_mailing(request):
    try:
        data = json.loads(request.body)
        version = data.get('version')
        email_send = data.get('email')
        mobile_version = data.get('mobile_version', None)  # Необязательный параметр
        mailing_type = data.get('mailing_type')  # Получаем тип рассылки из запроса
        additional_type = data.get('additional_type')

        send_test_email(version, email_send, mobile_version, mailing_type, additional_type)
        return JsonResponse({'message': 'Тестовое письмо успешно отправлено.'}, status=200)
    except json.JSONDecodeError as error_message:
        return JsonResponse({'error': 'Некорректный JSON: ' + str(error_message)}, status=400)
    except FileNotFoundError as error_message:
        return JsonResponse({'error': str(error_message)}, status=404)
    except smtplib.SMTPException as error_message:
        return JsonResponse({'error': str(error_message)}, status=500)
    except requests.exceptions.RequestException as error_message:
        return JsonResponse({'error': f"Ошибка связи с Яндекс.Диском: {str(error_message)}"}, status=500)
    except Exception as error_message:
        logger.error('Произошла ошибка при отправке письма: %s', str(error_message))
        return JsonResponse({'error': str(error_message)}, status=500)


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
            contact_name=data.get('name'),
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
        if 'name' in data:
            contact_card.contact_name = data['name']
        if 'position' in data:
            contact_card.contact_position = data['position']
        if 'email' in data:
            contact_card.contact_email = data['email']
        if 'number' in data:
            contact_card.contact_number = data['number']
        if 'notification_update' in data:
            contact_card.notification_update = data['notification_update']
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
        if 'manager' in data:
            service_card.manager = data['manager']
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
