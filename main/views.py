from django.shortcuts import render, redirect, get_object_or_404
from .models import ClientsList, ReportTicket, ReportDownloadjFrog, UsersBoardMaps, ClientsCard, ContactsCard, ReleaseInfo, ServiseCard, TechInformationCard, ConnectInfoCard, BMServersCard, Integration, ModuleCard, TechAccountCard, ConnectionInfo, TechNote
from .forms import ClientListForm, AdvancedSearchForm, ContactFormSet, ServiseCardForm, TechInformationCardForm, ContactForm, IntegrationForm, URLInputForm, ServerInputForm
from django.db import transaction
from django.db.models import QuerySet
from django.core import serializers
from django.forms.models import model_to_dict
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
# import ldap
import json
import os
from urllib.parse import unquote
from main.tasks import echo, send_test_email
from celery.result import AsyncResult
from django_celery_results.models import TaskResult
from scripts.update_tickets import update_tickets
from scripts.artifactory_downloads_log.monitor_log import analyze_logs_and_get_data
from scripts.obfuscate_db.obfuscate_mssql import DatabaseCleanerMsSQL
from scripts.obfuscate_db.obfuscate_postgresql import DatabaseCleanerPostgreSQL
from collections import defaultdict
import docx2txt


# def check_password_in_ldap(username, password):
#     try:
#         # Настройки для подключения к LDAP-серверу
#         ldap_server_uri = "ldap://corp.boardmaps.com"
#         ldap_bind_dn = "CN=Creg,OU=Service,OU=DashboardUsers,DC=corp,DC=boardmaps,DC=com"
#         ldap_bind_password = "pV4kh6d4c5JhM9"

#         # Установка соединения с LDAP-сервером
#         ldap_connection = ldap.initialize(ldap_server_uri)
#         ldap_connection.simple_bind_s(ldap_bind_dn, ldap_bind_password)

#         # Поиск пользователя по его sAMAccountName
#         user_search_base = "ou=DashboardUsers,dc=corp,dc=boardmaps,dc=com"
#         user_search_filter = f"(sAMAccountName={username})"
#         result = ldap_connection.search_s(user_search_base, ldap.SCOPE_SUBTREE, user_search_filter)

#         if result:
#             # Если пользователь найден, проверяем пароль
#             user_dn = result[0][0]
#             ldap_connection.simple_bind_s(user_dn, password)
#             ldap_connection.unbind_s()
#             return True
#     except ldap.INVALID_CREDENTIALS:
#         pass
#     except ldap.LDAPError as error_message:
#         print(f"LDAP Error: {error_message}")
#     finally:
#         ldap_connection.unbind_s()

#     return False

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('rememberMe')

        if not username or not password:
            error_message = "Пожалуйста, введите имя пользователя и пароль"
            return render(request, 'main/registration/login.html', {'error_message': error_message})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0) # Установка сессии до закрытия браузера, если "Запомнить меня" не выбран
                return redirect('home')
            else:
                error_message = "Ваш аккаунт отключен"

        else:
            # Проверяем пароль в LDAP
            if check_password_in_ldap(username, password):
                # Если пользователя с таким именем нет, создаем его и авторизуемся
                hashed_password = make_password(password)  # Создание хеша пароля
                user = User.objects.create(username=username, password=hashed_password)
                login(request, user)  # Авторизуемся под созданным пользователем
                return redirect('home')
            else:
                error_message = "Неправильное имя пользователя или пароль"

        return render(request, 'main/registration/login.html', {'error_message': error_message})

    # Если пользователь уже аутентифицирован, перенаправляем на главную страницу
    if request.user.is_authenticated:
        return redirect('home') # URL-паттерн

    return render(request, 'main/registration/login.html')


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
    return render(request, 'main/test/task_results.html', {'results': results})


def update_tickets_view(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            update_tickets(start_date, end_date)
            return render(request, 'main/report/success.html')
        except Exception as error_message:
            error_message = f'Произошла ошибка: {str(error_message)}'
            return render(request, 'main/report/error.html', {'error_message': error_message})

    return render(request, 'main/test/update_tickets.html')

def show_log_analysis(request):
    return render(request, 'main/report/artifactory_downloads_log.html')

def get_log_analysis_data(request):
    status, client_data = analyze_logs_and_get_data()
    if status == "Успешно":
        return JsonResponse({'client_data': client_data})
    else:
        return JsonResponse({'error': status}, status=400)


# @login_required
def index(request):
    # Добавляем переменную в контекст, которая указывает на то, что это главная страница
    context = {'hide_footer': True}
    return render(request, 'main/index.html', context)


def clients(request):
    clients = ClientsList.objects.all().prefetch_related('clients_card__contact_cards', 'clients_card__integration')  # Загрузите все карточки клиентов, связанные контакты и данные интеграции
    forms = {client.id: IntegrationForm(instance=client.clients_card.integration) for client in clients}  # Создаем словарь с формами интеграции для каждого клиента
    return render(request, 'main/clients.html', {'title': 'Список клиентов', 'clients': clients, 'forms': forms})


def get_contacts(request, client_id):
    client = ClientsList.objects.get(id=client_id)
    contacts = client.clients_card.contact_cards.all()
    template = loader.get_template('main/client/contacts_table.html')
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
            return render(request, 'main/report/error.html', {'error_message': error_message})
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
            return render(request, 'main/report/error.html', {'error_message': error_message})
    else:
        error_message = "Произошла ошибка при обработке формы."
        return render(request, 'main/report/error.html', {'error_message': error_message})

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
            return render(request, 'main/report/error.html', {'error_message': error_message})

    # Преобразуем список результатов в JSON
    results_json = json.dumps(rows)
    context = {'results_json': results_json}

    # Возвращаем шаблон search_results.html с данными для отображения результатов
    return render(request, 'main/search/search_results.html', context)


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
    return render(request, 'main/client/create_client.html', context)


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
    except ConnectInfoCard.DoesNotExist:
        # Создаем пустую запись для ConnectInfoCard, если она не существует
        connect_info_list = []

    try:
        bm_servers_list = BMServersCard.objects.filter(client_card=client.clients_card)
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
    except TechAccountCard.DoesNotExist:
        # Создаем пустую запись для TechAccountCard, если она не существует
        tech_account_list = []

    # Инициализация переменных
    file_name = ""
    file_path = "Нет документа"
    text = "Нет данных"

    try:
        connection_info = ConnectionInfo.objects.get(client_card__client_info=client)
        file_path = connection_info.file_path.url if connection_info.file_path else "Нет документа"
        # Получение названия файла из полного пути
        file_name = os.path.basename(connection_info.file_path.name) if connection_info.file_path else ""
        text = connection_info.text if connection_info.text else "Нет данных"
    except (ConnectionInfo.DoesNotExist, ValueError):
        connection_info = None

    try:
        tech_note = TechNote.objects.get(client_card=client.clients_card)
    except TechNote.DoesNotExist:
        # Создаем пустую запись для TechNote, если она не существует
        tech_note = TechNote.objects.create(client_card=client.clients_card, tech_note_text="Нет данных")
        
    # Добавьте выборку менеджеров
    managers = UsersBoardMaps.objects.filter(position='Менеджер')

    return render(request, 'main/client/client.html', {
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
        'connection_info': connection_info,
        'text': text,
        'file_name': file_name,
        'file_path': file_path,
        'tech_note': tech_note,
        'managers': managers,
    })


def document_preview(request, file_path):
    try:
        decoded_file_path = unquote(file_path)

        # Убираем начальную часть пути, соответствующую начальной директории
        relative_file_path = decoded_file_path.split('uploaded_files/', 1)[-1]

        full_file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_files', relative_file_path.replace("/", os.sep))
        
        if not os.path.exists(full_file_path):
            return HttpResponse("File not found", content_type='text/plain', status=404)

        content = docx2txt.process(full_file_path)
        
        return render(request, 'main/client/document_preview.html', {'content': content})
    except Exception as e:
        return HttpResponse(str(e), content_type='text/plain', status=500)


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
    
    return render(request, 'main/client/add_contact.html', {'title': 'Добавить контакт', 'client': client, 'contact_form': contact_form})


def upload_file(request):
    clients = ClientsList.objects.all()
    return render(request, 'main/client/upload_file.html', {'clients': clients})


def release_info(request):
    release_infos = ReleaseInfo.objects.order_by('-date')
    return render(request, 'main/report/release_info.html', {'release_infos': release_infos})


def report(request):
    now = timezone.now()
    # Первый день текущего года
    start_year = timezone.datetime(year=now.year, month=1, day=1)
    start_date = start_year.strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')

    report_tickets = list(ReportTicket.objects.filter(creation_date__range=[start_date, end_date]).values())
    report_tickets_json = json.dumps(report_tickets, default=str)
    return render(request, 'main/report/report.html', {'report_tickets': report_tickets_json})

def get_report_data(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    report_tickets = ReportTicket.objects.filter(report_date__range=[start_date, end_date]).values()
    return JsonResponse(list(report_tickets), safe=False)

# def report(request):
#     now = timezone.now()
#     start_week = now - timezone.timedelta(days=now.weekday())  # начало недели (понедельник)
#     report_tickets = list(ReportTicket.objects.filter(creation_date__range=[start_week, now]).values())
#     report_tickets_json = json.dumps(report_tickets, default=str)  # default=str используется для преобразования дат в строки
#     return render(request, 'main/report.html', {'report_tickets': report_tickets_json})

def report_tickets(request):
    report_tickets = list(ReportTicket.objects.all().values())

    report_tickets_json = json.dumps(report_tickets, default=str)
    return render(request, 'main/report/report_tickets.html', {'report_tickets': report_tickets_json})

def test(request):
    now = timezone.now()
    start_week = now - timezone.timedelta(days=now.weekday())
    start_date = start_week.strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')

    report_tickets = list(ReportTicket.objects.filter(creation_date__range=[start_week, now]).values())
    report_tickets_json = json.dumps(report_tickets, default=str)
    return render(request, 'main/test/test.html', {'report_tickets': report_tickets_json})


def report_jfrog(request):
    return render(request, 'main/report/report_jfrog.html')

def get_report_jfrog(request):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=2)

    if 'start' in request.GET and 'end' in request.GET:
        start_date = datetime.strptime(request.GET['start'], '%Y-%m-%d')
        end_date = datetime.strptime(request.GET['end'], '%Y-%m-%d')

    # Получаем QuerySet с фильтром по дате
    reports = ReportDownloadjFrog.objects.filter(date__range=[start_date, end_date])

    # Добавляем фильтр по учётным записям, если параметр присутствует
    if 'account' in request.GET:
        accounts = request.GET.getlist('account')  # Получает список всех 'account' параметров из URL
        reports = reports.filter(account_name__in=accounts)

    # Добавляем фильтр по версиям, если параметр присутствует
    if 'version' in request.GET:
        versions = request.GET.getlist('version')  # Получает список всех 'version' параметров из URL
        reports = reports.filter(version_download__in=versions)

    reports_list = [model_to_dict(report) for report in reports]

    return JsonResponse(reports_list, safe=False)

def get_unique_accounts(request):
    accounts = ReportDownloadjFrog.objects.values_list('account_name', flat=True).distinct()
    return JsonResponse(list(accounts), safe=False)

def get_unique_versions(request):
    versions = ReportDownloadjFrog.objects.values_list('version_download', flat=True).distinct()
    return JsonResponse(list(versions), safe=False)


def obfuscate_mssql(request):
    form = URLInputForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        service_url = form.cleaned_data['service_url']
        cleaner = DatabaseCleanerMsSQL(service_url)
        try:
            cleaner.connect()
            cleaner.clean()
            cleaner.close()
            # Если всё прошло успешно, используем шаблон успеха
            return render(request, 'main/report/success.html')
        except Exception as e:
            error_message = str(e)
            # Передаем ошибку в шаблон ошибки
            return render(request, 'main/report/error.html', {'error_message': error_message})

    # Если GET запрос или форма не валидна, показываем форму снова
    return render(request, 'main/test/obfuscate_mssql.html', {'form': form})

def obfuscate_postgresql(request):
    form = ServerInputForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        service_url = form.cleaned_data['service_url']
        cleaner = DatabaseCleanerPostgreSQL(service_url)
        try:
            cleaner.connect()
            cleaner.clean()
            cleaner.close()
            # Если всё прошло успешно, используем шаблон успеха
            return render(request, 'main/report/success.html')
        except Exception as e:
            error_message = str(e)
            # Передаем ошибку в шаблон ошибки
            return render(request, 'main/report/error.html', {'error_message': error_message})

    # Если GET запрос или форма не валидна, показываем форму снова
    return render(request, 'main/test/obfuscate_postgresql.html', {'form': form})


def mailing(request):
    return render(request, 'main/release/mailing.html')
