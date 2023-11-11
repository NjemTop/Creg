from django.http import HttpResponse, JsonResponse, HttpResponseServerError
import json
from main.models import ReportTicket
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from main.models import ClientsCard, TechAccountCard, ConnectInfoCard, ContactsCard
from django.contrib.auth.hashers import make_password, check_password


def creation_tickets(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        report_tickets = ReportTicket.objects.filter(creation_date__range=[start_date, end_date]).values()
        return JsonResponse(list(report_tickets), safe=False)
    except Exception as error_message:
        return HttpResponseServerError("Ошибка при получении данных:", str(error_message))

def open_tickets(request):
    try:
        open_report_tickets = ReportTicket.objects.exclude(status="Closed").values()
        return JsonResponse(list(open_report_tickets), safe=False)
    except Exception as error_message:
        return HttpResponseServerError("Ошибка при получении данных:", str(error_message))


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
def delete_connect_info(request, account_id):
    try:
        connect_info = ConnectInfoCard.objects.get(pk=account_id)
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
        if 'account' in data:
            contact_card.contact_position = data['position']
        if 'password' in data:
            contact_card.contact_email = data['email']
        if 'password' in data:
            contact_card.contact_number = data['number']
        if 'password' in data:
            contact_card.notification_update = data['notification_update']
        contact_card.save()
        return JsonResponse({'message': 'Контакт успешно обновлен'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)