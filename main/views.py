from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import ClientsList, ReportTicket, ReportDownloadjFrog, UsersBoardMaps, ClientsCard, ContactsCard, ReleaseInfo, ServiseCard, TechInformationCard, ConnectInfoCard, BMServersCard, Integration, ModuleCard, TechAccountCard, ConnectionInfo, TechNote
from .forms import ClientForm, ContactForm, ServiseCardForm, TechInformationCardForm, IntegrationForm, ModuleForm, CommandForm, AdvancedSearchForm, URLInputForm, ServerInputForm
from django.db import transaction
from django.forms import formset_factory
from django.forms import inlineformset_factory
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
import re
from django.core.management import call_command
from django.contrib.admin.views.decorators import staff_member_required
import io
import os
import threading
from urllib.parse import unquote
from main.tasks import create_hde_organization_task, add_user_tfs_task, add_user_jfrog_task, add_user_nextcloud_task, delete_user_nextcloud_task
from celery.result import AsyncResult
from scripts.helpdesk.update_tickets import TicketUpdater
from scripts.jfrog.artifactory_downloads_log.monitor_log import analyze_logs_and_get_data
from scripts.jfrog.add_user_JFrog import generate_random_password
from scripts.telegram.send_message import Alert
from scripts.email.email_send import EmailService
# from scripts.obfuscate_db.obfuscate_mssql import DatabaseCleanerMsSQL
from scripts.obfuscate_db.obfuscate_postgresql import DatabaseCleanerPostgreSQL
from collections import defaultdict
import docx2txt
import traceback


# Создаем объект класса Alert
alert = Alert()


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


# Функция для удаления ANSI escape-последовательностей из строки
def remove_ansi_escape_sequences(s):
    ansi_escape_pattern = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape_pattern.sub('', s)

@staff_member_required
def run_command(request):
    message = ''  # Сообщение с результатом выполнения команды
    if request.method == 'POST':
        form = CommandForm(request.POST)
        if form.is_valid():
            command_input = form.cleaned_data['command']
            # Разделяем введенную команду на имя команды и аргументы
            command_args = command_input.split()
            if command_args:  # Проверяем, есть ли что-то для выполнения
                out = io.StringIO()  # Создаем "фальшивый" файл для захвата вывода
                try:
                    # Вызываем команду с аргументами, распаковывая список аргументов
                    call_command(*command_args, stdout=out)
                    message = remove_ansi_escape_sequences(out.getvalue())  # Получаем вывод команды
                except Exception as e:
                    message = f"Ошибка при выполнении команды: {e}"
                finally:
                    out.close()
    else:
        form = CommandForm()
    return render(request, 'admin/run_command.html', {'form': form, 'message': message})


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


def add_user_nextcloud(request):
    if request.method == 'POST':
        client_name = request.POST.get('client_name')
        account_name = request.POST.get('account_name')
        group_name = request.POST.get('group_name')
        try:
            add_user_nextcloud_task.delay(client_name, account_name, group_name)
            return render(request, 'main/report/success.html')
        except Exception as error_message:
            error_message = f'Произошла ошибка: {str(error_message)}'
            return render(request, 'main/report/error.html', {'error_message': error_message})
    return render(request, 'main/test/add_user_nextcloud.html')

def delete_user_nextcloud(request):
    if request.method == 'POST':
        account_name = request.POST.get('account_name')
        group_name = request.POST.get('group_name')
        try:
            delete_user_nextcloud_task.delay(account_name, group_name)
            return render(request, 'main/report/success.html')
        except Exception as error_message:
            error_message = f'Произошла ошибка: {str(error_message)}'
            return render(request, 'main/report/error.html', {'error_message': error_message})
    return render(request, 'main/test/delete_user_nextcloud.html')


def update_tickets_view(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Преобразование дат в формат datetime с временем "00:00:00"
        start_datetime = f"{start_date} 00:00:00"
        end_datetime = f"{end_date} 23:59:59"

        try:
            updater = TicketUpdater()
            updater.update_tickets(start_datetime, end_datetime)
            return render(request, 'main/report/success.html')
        except Exception as error_message:
            error_message = f'Произошла ошибка: {str(error_message)}\n{traceback.format_exc()}'
            return render(request, 'main/report/error.html', {'error_message': error_message})

    return render(request, 'main/test/update_tickets.html')


# @login_required
def index(request):
    # managers = UsersBoardMaps.objects.filter(position='Менеджер')
    # tariff_plans = ServiseCard.objects.values_list('service_pack', flat=True).distinct()
    context = {
        # Добавляем переменную в контекст, которая указывает на то, что это главная страница
        'hide_footer': True,
        # 'managers': json.dumps(list(managers.values('id', 'name')), ensure_ascii=False),
        # 'tariff_plans': json.dumps(list(tariff_plans), ensure_ascii=False),
    }
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
            results = TechInformationCard.objects.all()

            if form.cleaned_data['integration']:
                results = results.filter(client_card__integration__isnull=False)
            if form.cleaned_data['module']:
                results = results.filter(client_card__module__isnull=False)
            if form.cleaned_data['plan_status']:
                results = results.filter(client_card__client_info__contact_status=True)
            if form.cleaned_data['server_version_checkbox']:
                server_version = form.cleaned_data['server_version_input']
                results = results.filter(server_version__icontains=server_version)
            if form.cleaned_data['filter_by_version']:
                version_prefix = form.cleaned_data['version']
                results = results.filter(server_version__startswith=version_prefix)
            if form.cleaned_data['filter_by_manager']:
                manager = form.cleaned_data['manager']
                results = results.filter(client_card__servise_card__manager=manager)
            if form.cleaned_data['filter_by_tariff_plan']:
                tariff_plan = form.cleaned_data['tariff_plan']
                results = results.filter(client_card__servise_card__service_pack=tariff_plan)

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
                'manager': result.client_card.servise_card.manager.name if result.client_card.servise_card.manager else '',
                'service_pack': result.client_card.servise_card.service_pack,
                'notes': result.client_card.client_info.notes,
            }
            rows.append(row)
        except Exception as error:
            error_message = f"Произошла ошибка при обработке результатов: {str(error)}"
            return render(request, 'main/report/error.html', {'error_message': error_message})

    # Преобразуем список результатов в JSON
    results_json = json.dumps(rows)
    context = {
        'results_json': results_json,
        'form': form,
        'managers': json.dumps(list(UsersBoardMaps.objects.filter(position='Менеджер').values('id', 'name')), ensure_ascii=False),
        'tariff_plans': json.dumps(list(ServiseCard.objects.values_list('service_pack', flat=True).distinct()), ensure_ascii=False),
    }

    return render(request, 'main/search/search_results.html', context)


def search_versions(request):
    query = request.GET.get('q', '')
    if query:
        versions = TechInformationCard.objects.filter(server_version__icontains=query).values_list('server_version', flat=True).distinct()
        return JsonResponse(list(versions), safe=False)
    return JsonResponse([], safe=False)


def update_integration(request, client_id):
    form = IntegrationForm(request.POST, instance=ClientsList.objects.get(id=client_id).clients_card.integration)
    if form.is_valid():
        form.save()
    return redirect('clients')


def get_module_names(module_form):
    module_names = {}
    for field in module_form:
        if getattr(module_form.instance, field.name):
            module_names[module_form.fields[field.name].label] = True
    return module_names


@transaction.atomic
def create_client(request):
    # Создаем формсет для контактов с возможностью динамического добавления и удаления форм
    ContactFormSet = inlineformset_factory(ClientsCard, ContactsCard, form=ContactForm, extra=0, can_delete=False)

    contactFormSet = None

    if request.method == 'POST':
        # Инициализируем формы с данными из POST запроса
        clientForm = ClientForm(request.POST)
        techInformationCardForm = TechInformationCardForm(request.POST)
        moduleForm = ModuleForm(request.POST)

        # Проверяем, валидны ли все формы
        if clientForm.is_valid() and techInformationCardForm.is_valid() and moduleForm.is_valid():
            try:
                # Сохраняем основную информацию о клиенте
                client_instance = clientForm.save()
                
                try:
                    # Генерируем пароль и сохраняем его в объект клиента
                    client_instance.password = generate_random_password()
                    client_instance.save()

                    # Создаём задачу на создание пользователя в jFrog
                    add_user_jfrog_task.apply_async((client_instance.short_name, client_instance.password), countdown=60)
                except Exception as error_message:
                    # В случае ошибки отправляем алерт с сообщением об ошибке
                    alert.send_telegram_message("320851571", error_message)

                try:
                    # Создаём задачу на создание пользователя в TFS
                    add_user_tfs_task.apply_async((client_instance.client_name,), countdown=120)
                except Exception as error_message:
                    # В случае ошибки отправляем алерт с сообщением об ошибке
                    alert.send_telegram_message("320851571", error_message)

                try:
                    # Создаём задачу на создание пользователя в NextCloud
                    add_user_nextcloud_task.apply_async((client_instance.client_name, client_instance.short_name, client_instance.short_name), countdown=180)
                except Exception as error_message:
                    # В случае ошибки отправляем алерт с сообщением об ошибке
                    alert.send_telegram_message("320851571", error_message)

                # Создаем связанный экземпляр ClientsCard для нового клиента
                clients_card_instance = ClientsCard.objects.create(client_info=client_instance)

                # Сохраняем техническую информацию, связанную с клиентом
                tech_info_instance = techInformationCardForm.save(commit=False)
                tech_info_instance.client_card = clients_card_instance
                tech_info_instance.save()

                try:
                    # Создаём задачу на создание пользователя в HDE
                    create_hde_organization_task.apply_async((client_instance.client_name, tech_info_instance.server_version), countdown=60)
                except Exception as error_message:
                    # В случае ошибки отправляем алерт с сообщением об ошибке
                    alert.send_telegram_message("320851571", error_message)

                # Сохраняем информацию о модулях
                module_instance = moduleForm.save(commit=False)
                module_instance.client_card = clients_card_instance
                module_instance.save()

                # Обрабатываем формсет контактов
                contactFormSet = ContactFormSet(request.POST, instance=clients_card_instance)
                print("Contact forms count:", contactFormSet.total_form_count())
                if contactFormSet.is_valid():
                    print(contactFormSet)
                    contactFormSet.save()
                else:
                    print(contactFormSet.errors)

                try:
                    module_names = get_module_names(moduleForm)

                    email_service = EmailService()
                    result = email_service.send_client_creation_email(
                        client_instance,
                        tech_info_instance,
                        [form.cleaned_data for form in contactFormSet],
                        module_names
                    )
                    if result is not None:
                        # В случае ошибки отправляем алерт с сообщением об ошибке
                        alert.send_telegram_message("320851571", result)
                except Exception as error_message:
                    # В случае ошибки отправляем алерт с сообщением об ошибке
                    alert.send_telegram_message("320851571", error_message)

                # Перенаправляем на страницу клиента после успешного создания
                return redirect(reverse('client', kwargs={'client_id': client_instance.id}))
            except Exception as error_message:
                # В случае ошибки возвращаем пользователя на страницу с сообщением об ошибке
                return render(request, 'main/report/error.html', {'error_message': str(error_message)})
    else:
        # Если запрос не POST, отображаем пустые формы
        clientForm = ClientForm()
        techInformationCardForm = TechInformationCardForm()
        moduleForm = ModuleForm()
        contactFormSet = ContactFormSet()

    # Рендерим шаблон с формами
    return render(request, 'main/create_client.html', {
        'clientForm': clientForm,
        'techInformationCardForm': techInformationCardForm,
        'moduleForm': moduleForm,
        'contactFormSet': contactFormSet,
    })


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
        servise = ServiseCard.objects.create(
            client_card=client.clients_card,
            service_pack="Нет данных",
            manager=None,
            loyal="Нет данных"
        )

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

    # Подсчет всех открытых тикетов
    open_tickets_count = ReportTicket.objects.exclude(status__in=["Closed", "Выполнено"]).count()

    # Подсчет открытых тикетов с заполненным полем ci
    open_ci_tickets_count = ReportTicket.objects.exclude(status__in=["Closed", "Выполнено"]).exclude(ci__isnull=True).exclude(ci='').count()

    return render(request, 'main/report/report.html', {
        'report_tickets': report_tickets_json,
        'open_tickets_count': open_tickets_count,
        'open_ci_tickets_count': open_ci_tickets_count
    })

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
