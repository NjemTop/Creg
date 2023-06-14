from django.shortcuts import render, redirect
from .models import ClientsList, ReportTicket, ClientsCard, ContactsCard, ReleaseInfo, ServiseCard, TechInformationCard, ConnectInfoCard, BMServersCard, Integration, ModuleCard, TechAccountCard, ConnectionInfo, TechNote
from .forms import ClientListForm, AdvancedSearchForm, ContactFormSet, ServiseCardForm, TechInformationCardForm, ContactForm, IntegrationForm
from django.db import transaction
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from main.tasks import echo, send_test_email
from celery.result import AsyncResult
from django_celery_results.models import TaskResult


def test_task(request):
    task = echo.delay(4, 4)
    result = AsyncResult(id=task.task_id)
    
    if result.failed():
        response = f"Task ID: {task.task_id}, Task Status: {result.status}, Error: {result.result}"
    else:
        response = f"Task ID: {task.task_id}, Task Status: {result.status}, Task Result: {result.result}"
    
    return HttpResponse(response)

def get_task_info(request, task_id):
    task = AsyncResult(task_id)
    info = {
        'state': task.state,
        'result': task.result,
    }
    return JsonResponse(info)

def test_send_email_task(request):
    task = send_test_email.delay('oleg.eliseev@boardmaps.ru')
    return JsonResponse({'task_id': task.id}, status=202)

def task_results(request):
    results = TaskResult.objects.all()
    return render(request, 'main/results.html', {'results': results})


def index(request):
    return render(request, 'main/index.html')


def clients(request):
    clients = ClientsList.objects.all().prefetch_related('clients_card__contact_cards', 'clients_card__integration')  # Загрузите все карточки клиентов, связанные контакты и данные интеграции
    forms = {client.id: IntegrationForm(instance=client.clients_card.integration) for client in clients}  # Создаем словарь с формами интеграции для каждого клиента
    return render(request, 'main/clients.html', {'title': 'Список клиентов', 'clients': clients, 'forms': forms})


def get_contacts(request, client_id):
    client = ClientsList.objects.get(id=client_id)
    contacts = client.clients_card.contact_cards.all()
    template = loader.get_template('main/contacts_table.html')
    context = {'contacts': contacts}
    contacts_table = template.render(context, request)
    return HttpResponse(contacts_table)


def search_results(request):
    # Получаем данные формы из GET-запроса
    form = AdvancedSearchForm(request.GET)

    # Проверяем, установлен ли флаг "show_all"
    # Если "show_all" равно "true", возвращаем все записи из TechInformationCard
    # В противном случае используем данные формы для поиска
    show_all = request.GET.get('show_all', 'false') == 'true'

    # Если установлен флаг "show_all"
    if show_all:
        try:
            results = TechInformationCard.objects.all()
        except Exception as error:
            error_message = f"Произошла ошибка при получении всех записей: {str(error)}"
            return render(request, 'main/error.html', {'error_message': error_message})
    # Если форма действительна
    elif form.is_valid():
        try:
            # Получаем значения чекбокса и поля ввода для версии сервера
            server_version_checkbox = form.cleaned_data.get('serverVersionCheckbox')
            server_version_input = form.cleaned_data.get('serverVersionInput')
            
            # Если чекбокс версии сервера отмечен, используем введенную версию сервера для поиска записей
            if server_version_checkbox:
                results = TechInformationCard.objects.filter(server_version=server_version_input)
        except Exception as error:
            error_message = f"Произошла ошибка при обработке данных формы: {str(error)}"
            return render(request, 'main/error.html', {'error_message': error_message})
    else:
        error_message = "Произошла ошибка при обработке формы."
        return render(request, 'main/error.html', {'error_message': error_message})

    # Подготавливаем данные для отправки в шаблон
    rows = []
    for result in results:
        try:
            # Создаем словарь для каждого результата и добавляем его в список
            row = {
            'client_name': result.client_card.client_info.client_name,
            'server_version': result.server_version,
            'update_date': result.update_date.strftime('%Y-%m-%d'),
            # Добавьте другие поля, если необходимо
            }
            rows.append(row)
        except Exception as error:
            error_message = f"Произошла ошибка при обработке результатов: {str(error)}"
            return render(request, 'main/error.html', {'error_message': error_message})

    # Преобразуем список результатов в JSON
    results_json = json.dumps(rows)
    context = {'results_json': results_json}

    # Возвращаем шаблон search_results.html с данными для отображения результатов
    return render(request, 'main/search_results.html', context)


def update_integration(request, client_id):
    form = IntegrationForm(request.POST, instance=ClientsList.objects.get(id=client_id).clients_card.integration)
    if form.is_valid():
        form.save()
    return redirect('clients')


@transaction.atomic
def create_client(request):
    error = ''  # Инициализация переменной для хранения ошибки
    form_client = None  # Инициализация переменной для хранения формы клиента

    if request.method == 'POST':
        form_client = ClientListForm(request.POST)  # Создание формы клиента на основе POST-данных
        contact_formset = ContactFormSet(request.POST, prefix='contacts')  # Создание формсета контактов на основе POST-данных с префиксом 'contacts'
        servise_form = ServiseCardForm(request.POST)  # Создание формы сервисной карты на основе POST-данных
        tech_info_form = TechInformationCardForm(request.POST) # Создание формы технической информации на основе POST-данных

        if form_client.is_valid() and contact_formset.is_valid() and servise_form.is_valid() and tech_info_form.is_valid():
            # Если все формы валидны, выполняется сохранение данных

            client_list = form_client.save()  # Сохранение данных клиента
            client_card = ClientsCard.objects.create(client_info=client_list)  # Создание записи о клиенте в модели ClientsCard

            for form in contact_formset:
                contact = form.save(commit=False)  # Создание объекта контакта без сохранения в базу данных
                contact.client_card = client_card  # Привязка контакта к клиентской карте
                contact.save()  # Сохранение контакта в базу данных

            # Создание объекта сервисной карты без сохранения в базу данных
            servise_card = servise_form.save(commit=False)
            servise_card.client_card = client_card  # Привязка сервисной карты к клиентской карте
            servise_card.save()  # Сохранение сервисной карты в базу данных

            # Создание объекта технической информации без сохранения в базу данных
            tech_info = tech_info_form.save(commit=False)
            tech_info.client_card = client_card
            tech_info.save()

            return redirect('clients')  # Перенаправление на страницу со списком клиентов
        else:
            error = 'Ошибка при заполнении формы данных'  # Установка сообщения об ошибке
            raise ValueError('Ошибка при сохранении данных о контактах')  # Генерация исключения ValueError при ошибке валидации форм

    else:
        form_client = ClientListForm()  # Создание пустой формы клиента
        contact_formset = ContactFormSet(prefix='contacts')  # Создание пустого формсета контактов с префиксом 'contacts'
        servise_form = ServiseCardForm()  # Создание пустой формы сервисной карты
        tech_info_form = TechInformationCardForm() # Создание пустой формы технической информации

    context = {
        'form_client': form_client,
        'contact_formset': contact_formset,
        'servise_form': servise_form,
        'tech_info_form': tech_info_form,
        'error': error,
        'contact_formset_total_form_count': contact_formset.total_form_count,  # Передача количества форм в формсете в контекст
        'contact_formset_max_num': contact_formset.max_num,  # Передача максимального количества форм в формсете в контекст
    }
    return render(request, 'main/create_client.html', context)  # Возвращение ответа с рендерингом шаблона 'create_client.html' и передачей контекста


def client(request, client_id):
    client = ClientsList.objects.get(id=client_id)
    
    try:
        contacts_list = ContactsCard.objects.filter(client_card=client.clients_card)
    except ContactsCard.DoesNotExist:
        # Создаем пустую запись для ContactsCard, если она не существует
        contacts_list = []

    try:
        integration = Integration.objects.get(client_card__client_info=client)
    except Integration.DoesNotExist:
        # Создаем пустую запись для Integration, если она не существует
        integration = Integration.objects.create(client_card=client.clients_card, elasticsearch=False, ad=False, adfs=False,
                                                 oauth_2=False, module_translate=False, ms_oos=False, exchange=False,
                                                 office_365=False, sfb=False, zoom=False, teams=False, smtp=False,
                                                 cryptopro_dss=False, cryptopro_csp=False, smpp=False, limesurvey=False)

    try:
        module = ModuleCard.objects.get(client_card=client.clients_card)
    except ModuleCard.DoesNotExist:
        # Создаем пустую запись для ModuleCard, если она не существует
        module = ModuleCard.objects.create(client_card=client.clients_card, translate=False, electronic_signature=False,
                                           action_items=False, limesurvey=False, advanced_voting=False,
                                           advanced_work_with_documents=False, advanced_access_rights_management=False,
                                           visual_improvements=False, third_party_product_integrations=False,
                                           microsoft_enterprise_product_integrations=False,
                                           microsoft_office_365_integration=False)

    try:
        tech_info = TechInformationCard.objects.get(client_card=client.clients_card)
    except TechInformationCard.DoesNotExist:
        # Создаем пустую запись для TechInformationCard, если она не существует
        tech_info = TechInformationCard.objects.create(client_card=client.clients_card, server_version="Нет данных",
                                                       update_date=None, api=False, ipad="Нет данных", android="Нет данных",
                                                       mdm="Нет данных", localizable_web=False, localizable_ios=False,
                                                       skins_web=False, skins_ios=False)

    try:
        connect_info_list = ConnectInfoCard.objects.filter(client_card=client.clients_card)
        # if not connect_info_list:
        #     # Создаем пустую запись для ConnectInfoCard, если она не существует
        #     ConnectInfoCard.objects.create(client_card=client.clients_card, contact_info_name="Нет данных",
        #                                    contact_info_account="Нет данных",
        #                                    contact_info_password="Нет данных")
    except ConnectInfoCard.DoesNotExist:
        connect_info_list = []

    try:
        bm_servers_list = BMServersCard.objects.filter(client_card=client.clients_card)
        # if not bm_servers_list:
        #     # Создаем пустую запись для BMServersCard, если она не существует
        #     BMServersCard.objects.create(client_card=client.clients_card, bm_servers_circuit="Нет данных",
        #                                   bm_servers_servers_name="Нет данных",
        #                                   bm_servers_servers_adress="Нет данных", bm_servers_role="Нет данных")
    except BMServersCard.DoesNotExist:
        # Создаем пустую запись для BMServersCard, если она не существует
        bm_servers_list = []

    try:
        servise = ServiseCard.objects.get(client_card=client.clients_card)
    except ServiseCard.DoesNotExist:
        # Создаем пустую запись для ServiseCard, если она не существует
        servise = ServiseCard.objects.create(client_card=client.clients_card, service_pack="Нет данных",
                                             manager="Нет данных", loyal="Нет данных")

    try:
        tech_account_list = TechAccountCard.objects.filter(client_card=client.clients_card)
        # if not tech_account_list:
        #     # Создаем пустую запись для TechAccountCard, если она не существует
        #     TechAccountCard.objects.create(client_card=client.clients_card, contact_info_disc="Нет данных",
        #                                    contact_info_account="Нет данных",
        #                                    contact_info_password="Нет данных")
    except TechAccountCard.DoesNotExist:
        # Создаем пустую запись для TechAccountCard, если она не существует
        tech_account_list = []

    try:
        connection_info = ConnectionInfo.objects.get(client_card__client_info=client)
        file_path = connection_info.file_path.url
        text = connection_info.text
    except ConnectionInfo.DoesNotExist:
        file_path = "Нет документа"
        text = "Нет данных"
    except ValueError:
        file_path = "Нет документа"
        text = "Нет данных"

    try:
        tech_note = TechNote.objects.get(client_card=client.clients_card)
    except TechNote.DoesNotExist:
        # Создаем пустую запись для TechNote, если она не существует
        tech_note = TechNote.objects.create(client_card=client.clients_card, tech_note_text="Нет данных")

    return render(request, 'main/client.html', {
        'title': 'Информация о клиенте',
        'client': client,
        'contacts_list': contacts_list,
        'integration': integration,
        'module': module,
        'tech_info': tech_info,
        'connect_info_list': connect_info_list,
        'bm_servers_list': bm_servers_list,
        'servise': servise,
        'tech_account_list': tech_account_list,
        'file_path': file_path,
        'text': text,
        'tech_note': tech_note,
    })


def add_contact(request, client_id):
    client = get_object_or_404(ClientsList, id=client_id)
    
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact = contact_form.save(commit=False)
            contact.client_card = client.clients_card
            contact.save()
            return redirect('client', client_id=client_id)
    else:
        contact_form = ContactForm()
    
    return render(request, 'main/add_contact.html', {'title': 'Добавить контакт', 'client': client, 'contact_form': contact_form})


def upload_file(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/upload_file.html', {'clients': clients})


def release_info(request):
    release_infos = ReleaseInfo.objects.order_by('-date')
    return render(request, 'main/release_info.html', {'release_infos': release_infos})


def report(request):
    now = timezone.now()
    start_week = now - timezone.timedelta(days=now.weekday())  # начало недели (понедельник)
    report_tickets = list(ReportTicket.objects.filter(creation_date__range=[start_week, now]).values())
    report_tickets_json = json.dumps(report_tickets, default=str)  # default=str используется для преобразования дат в строки
    return render(request, 'main/report.html', {'report_tickets': report_tickets_json})
