from celery import shared_task
from django.utils import timezone
from .models import ClientsList, ContactsCard, TechInformationCard, ServiseCard, UsersBoardMaps, TaskExecution, ClientSyncStatus
from scripts.helpdesk.sync_contacts import get_user_from_ticket_system, update_ticket_system_user, create_user_in_ticket_system, update_user_status
from scripts.helpdesk.sync_server_version import update_organization_version, find_organization_id
from scripts.helpdesk.sync_manager import update_organization_manager
from scripts.helpdesk.create_new_client import create_organization_in_hde
from scripts.helpdesk.sync_company import update_organization_status
from scripts.helpdesk.update_tickets import TicketUpdater
from scripts.jfrog.add_user_JFrog import authenticate, create_user
from scripts.tfs.create_client_TFS import trigger_tfs_pipeline
from scripts.tfs.create_cr import create_change_request, RequestError
from scripts.tfs.check_pipeline_status import monitor_pipeline_completion
from scripts.nextcloud.manager_nextcloud import NextCloudManager
from scripts.jfrog.artifactory_downloads_log.monitor_log import analyze_logs_and_update_db
from requests.exceptions import HTTPError, ConnectionError
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
from .utils import load_config
import traceback
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

load_dotenv()


@shared_task
def artifactory_downloads_log():
    try:
        scripts_info_logger.info(f"Запуск задачи по обновлению информации о скачивании в jFrog")
        analyze_logs_and_update_db()
        scripts_info_logger.info(f"Задачи по обновлению информации о скачивании в jFrog завершилась")
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")


@shared_task
def update_tickets():
    try:
        # Получение текущей даты
        today = datetime.now()
        start_datetime = today.strftime('%Y-%m-%d 00:00:00')
        end_datetime = today.strftime('%Y-%m-%d 23:59:59')
        
        scripts_info_logger.info(f"Запуск задачи по обновлению заявок для диапазона: {start_datetime} - {end_datetime}")
        updater = TicketUpdater()
        
        updater.update_tickets(start_datetime, end_datetime)
        scripts_info_logger.info(f"Задача по обновлению заявок успешно выполнена.")
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

@shared_task
def clean_up_tickets():
    try:
        scripts_info_logger.info(f"Запуск задачи по проверке открытых заявок.")
        updater = TicketUpdater()
        
        updater.clean_up_tickets()
        scripts_info_logger.info(f"Задача по проверке открытых заявок успешно выполнена.")
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")


@shared_task(bind=True, autoretry_for=(HTTPError, ConnectionError), retry_backoff=True, max_retries=5)
def sync_contacts_with_ticket_system_task(self):
    """
    Задача Celery для синхронизации обновленных контактов с тикет системой.
    Проверяет контакты, обновленные за последний час, и синхронизирует их с тикет системой.
    """
    with requests.Session() as session:
        session.auth = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
        try:
            scripts_info_logger.info(f"Запуск задачи по синхронизации контактов Creg с HDE системой")
            # Время последнего запуска задачи
            last_sync_time = timezone.now() - timedelta(hours=1)

            # Находим контакты, которые были обновлены с момента последней синхронизации
            updated_contacts = ContactsCard.objects.filter(last_updated__gte=last_sync_time)

            for contact in updated_contacts:
                try:
                    scripts_info_logger.info(f"Обработка контакта {contact.id}...")

                    # Преобразуем объект контакта в словарь
                    contact_dict = {
                        'firstname': contact.firstname,
                        'lastname': contact.lastname,
                        'contact_email': contact.contact_email,
                        'contact_number': contact.contact_number
                    }

                    # Логика получения данных пользователя из тикет системы
                    ticket_system_user = get_user_from_ticket_system(session, contact.contact_email)
                    if ticket_system_user:
                        # Логика обновления данных пользователя в тикет системе
                        update_ticket_system_user(session, ticket_system_user['id'], contact_dict)
                    else:
                        scripts_info_logger.info(f"Начат процесс создания нового пользователя {contact.id} в тикет системе...")
                        # Пользователь не найден, создаем нового пользователя
                        create_user_in_ticket_system(session, contact_dict, contact.client_card.client_info.contact_status)
                    scripts_info_logger.info(f"Контакт {contact.id} успешно обработан.")
                except Exception as error_message:
                    scripts_error_logger.error(f"Ошибка при обработке контакта {contact.id}: {error_message}")
                    scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

        except Exception as error_message:
            scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
    
    scripts_info_logger.info(f"Задача по синхронизации контактов Creg с HDE системой завершена.")

@shared_task(bind=True, autoretry_for=(HTTPError, ConnectionError), retry_backoff=True, max_retries=5)
def sync_server_versions_with_ticket_system(self):
    """
    Задача Celery для синхронизации информации о версиях сервера с тикет-системой.
    """
    with requests.Session() as session:
        session.auth = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
        try:
            scripts_info_logger.info(f"Запуск задачи по синхронизации версии сервера Creg с HDE системой")
            # Время последнего запуска задачи
            last_sync_time = timezone.now() - timedelta(hours=2)

            updated_tech_info = TechInformationCard.objects.filter(last_updated__gte=last_sync_time)

            for tech_info in updated_tech_info:
                client_name = tech_info.client_card.client_info.client_name
                try:
                    org_id = find_organization_id(session, client_name)
                    if org_id:
                        update_organization_version(session, org_id, tech_info.server_version)
                    else:
                        scripts_error_logger.error(f"Не найден org_id для версии сервера {tech_info.id}")
                except Exception as error_message:
                    scripts_error_logger.error(f"Ошибка при обновлении версии сервера {tech_info.id}: {error_message}")
                    scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

        except Exception as error_message:
            scripts_error_logger.error(f"Ошибка при запуске задачи: {error_message}")
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

    scripts_info_logger.info(f"Задача по синхронизации версий сервера завершена.")

@shared_task(bind=True, autoretry_for=(HTTPError, ConnectionError), retry_backoff=True, max_retries=5)
def sync_manager_with_ticket_system(self):
    """
    Задача Celery для синхронизации информации о менеджерах с тикет-системой.
    """
    with requests.Session() as session:
        session.auth = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
        try:
            scripts_info_logger.info("Запуск задачи по синхронизации менеджеров Creg с HDE системой")
            last_sync_time = timezone.now() - timedelta(hours=2)
            updated_service_cards = ServiseCard.objects.filter(last_updated__gte=last_sync_time)

            for service_card in updated_service_cards:
                client_name = service_card.client_card.client_info.client_name
                if not service_card.manager:
                    scripts_error_logger.error(f"Для информацией обслуживания клиента {client_name} не указан менеджер.")
                    continue

                if not service_card.manager.agent_id:
                    scripts_error_logger.error(f"Для менеджера {service_card.manager.id} не указан 'ID в тикет системе'.")
                    continue

                try:
                    org_id = find_organization_id(session, client_name)
                    if org_id:
                        update_organization_manager(session, org_id, service_card.manager)
                    else:
                        scripts_error_logger.error(f"Не найден org_id для {client_name}")
                except Exception as error:
                    scripts_error_logger.error(f"Ошибка при обновлении менеджера {client_name}: {str(error)}")
                    scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

        except Exception as error:
            scripts_error_logger.error(f"Ошибка при запуске задачи: {str(error)}")
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

    scripts_info_logger.info(f"Задача по синхронизации менеджеров завершена.")


@shared_task(bind=True, autoretry_for=(HTTPError, ConnectionError), retry_backoff=True, max_retries=5)
def sync_client_statuses(self):
    """
    Проверяет и обновляет статусы клиентов и их сотрудников в HDE.
    Если компании нет, то создаёт организацию.
    """
    with requests.Session() as session:
        scripts_info_logger.info("Запуск задачи по синхронизации статуса компании")
        session.auth = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
        last_sync_time = timezone.now() - timedelta(hours=2)
        clients = ClientsList.objects.filter(last_updated__gte=last_sync_time)

        # Диагностика перед вызовом load_config
        config = load_config()
        assigned_to = config['TFS']['assigned_to_product']

        # Инициализация NextCloudManager
        nextcloud_config = config['NEXT_CLOUD']
        nextcloud_manager = NextCloudManager(nextcloud_config['URL'], nextcloud_config['USER'], nextcloud_config['PASSWORD'])

        for client in clients:
            scripts_info_logger.info(f"client: {client}")
            # Проверяем время последней синхронизации для этого клиента
            sync_status, created = ClientSyncStatus.objects.get_or_create(client=client)
            if not created and sync_status.last_synced >= client.last_updated:
                scripts_info_logger.info(f"Клиент {client.client_name} уже синхронизирован недавно. Пропуск.")
                continue

            try:
                scripts_info_logger.info(f"У клиента {client.client_name} было изменение, начат процесс синхронизации.")
                org_id = find_organization_id(session, client.client_name)
                if org_id:
                    update_successful, response_data = update_organization_status(session, org_id, client.contact_status)
                    if update_successful:
                        # Извлекаем и обновляем статусы сотрудников
                        employees = response_data['data'].get('employees', [])
                        for emp_id in employees:
                            update_user_status(session, emp_id, 'active' if client.contact_status else 'disabled')
                    else:
                        scripts_error_logger.error(f"Не удалось обновить статус для {client.client_name}")
                else:
                    scripts_error_logger.error(f"Организация не найдена для {client.client_name}")
                    # Получаем контакты клиента через ClientsCard и ContactsCard
                    client_card = client.clients_card
                    contacts = list(client_card.contact_cards.all().values())
                    service_card = client_card.servise_card
                    tech_info_card = client_card.tech_information

                    manager_name = service_card.manager.name if service_card.manager else "Менеджера пока нет"
                    service_pack = service_card.service_pack
                    server_version = tech_info_card.server_version

                    # Извлекаем домены из email контактов
                    domains = ', '.join(set('@' + contact['contact_email'].split('@')[-1] for contact in contacts))
                    # Передаем список контактов клиенту в задачу создания организации
                    create_hde_organization_task.delay(client.client_name, server_version, contacts, client.contact_status, manager_name, service_pack, domains)

                # Если статус клиента неактивен, создаём Change Request в Azure DevOps и удаляем из NextCloud
                if not client.contact_status:
                    try:
                        change_request_info = create_change_request(client.client_name, assigned_to)
                        scripts_info_logger.info(f"Создан Change Request: {change_request_info}")
                    except RequestError as e:
                        scripts_error_logger.error(f"Ошибка при создании Change Request для клиента {client.client_name}: {str(e)}")

                    try:
                        user_name = client.short_name
                        group_name = client.short_name
                        if nextcloud_manager.execute_deletion(user_name, group_name):
                            scripts_info_logger.info(f"Учётная запись {user_name} и группа {group_name} успешно удалены из NextCloud.")
                        else:
                            scripts_error_logger.error(f"Ошибка при удалении учётной записи {user_name} и группы {group_name} из NextCloud.")
                    except Exception as e:
                        scripts_error_logger.error(f"Ошибка при удалении клиента {client.client_name} из NextCloud: {str(e)}")
                        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

                # Обновляем время последней синхронизации для клиента
                sync_status.last_synced = timezone.now()
                sync_status.save()
            except Exception as error:
                scripts_error_logger.error(f"Ошибка при обработке клиента {client.client_name}: {str(error)}")
                scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

    scripts_info_logger.info("Задача по синхронизации компании завершена.")


@shared_task(bind=True, autoretry_for=(HTTPError, ConnectionError), retry_backoff=True, max_retries=5)
def create_hde_organization_task(self, organization_name, server_version, contacts, client_status, manager_name, service_pack, domains):
    """
    Задача Celery для создания организации в HDE и учетных записей.
    :param organization_name: Название организации для создания
    :param server_version: Версия сервера для организации
    :param contacts: Список контактов для создания учетных записей
    :param client_status: Статус клиента для проверки перед созданием учетных записей
    :param manager_name: Имя менеджера для организации
    :param service_pack: Тарифный план для организации
    :param domains: Домены организации через запятую
    """
    with requests.Session() as session:
        session.auth = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
        try:
            scripts_info_logger.info(f"Запуск задачи по созданию компании {organization_name} в HDE")
            org_id = create_organization_in_hde(session, organization_name, server_version, manager_name, service_pack, domains)
            if org_id:
                scripts_info_logger.info(f"Компания {organization_name} успешно создана со статусом 'Активен'")
                # Вызываем задачу создания учетных записей после успешного создания организации
                create_user_accounts_task.delay(organization_name, contacts, client_status, org_id)
            else:
                scripts_error_logger.error("Ошибка при создании организации")

        except Exception as error:
            scripts_error_logger.error(f"Ошибка при запуске задачи: {str(error)}")
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")


@shared_task(bind=True, autoretry_for=(HTTPError, ConnectionError), retry_backoff=True, max_retries=5)
def create_user_accounts_task(self, organization_name, contacts, client_status, org_id):
    """
    Задача Celery для создания учетных записей в тикет системе для указанной организации.
    :param organization_name: Название организации для создания учетных записей
    :param contacts: Список контактов для создания учетных записей
    :param client_status: Статус клиента для проверки перед созданием учетных записей
    :param org_id: ID организации для привязки пользователей
    """
    with requests.Session() as session:
        session.auth = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
        try:
            scripts_info_logger.info(f"Запуск задачи по созданию учетных записей для компании {organization_name}")
            for contact in contacts:
                create_user_in_ticket_system(session, contact, client_status, org_id)
            scripts_info_logger.info(f"Учетные записи для компании {organization_name} успешно созданы")
        except Exception as error:
            scripts_error_logger.error(f"Ошибка при создании учетных записей для {organization_name}: {str(error)}")
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")


@shared_task
def add_user_jfrog_task(client_name, password):
    try:
        scripts_info_logger.info(f"Запуск задачи по созданию нового пользователя {client_name} в jFrog")
        # Вызов функций авторизации
        cookies = authenticate()
        if cookies:
            status_code = create_user(client_name, password, cookies)
            if status_code:
                scripts_info_logger.info(f"Пользователь {client_name} с паролем {password} успешно создан. Код ответа: {status_code}")
            else:
                scripts_error_logger.error("Ошибка при создании пользователя")
        else:
            scripts_error_logger.error("Ошибка авторизации")
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при выполнении задачи: {error_message}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")


@shared_task
def add_user_tfs_task(client_name):
    try:
        scripts_info_logger.info(f"Запуск задачи по созданию нового пользователя {client_name} в TFS")
        run_id = trigger_tfs_pipeline(client_name)
        if run_id:
            scripts_info_logger.info(f"Пайплайн для клиента {client_name} успешно создан. Run ID: {run_id}")
            monitor_pipeline_task.delay(run_id)  # Асинхронный вызов задачи мониторинга
        else:
            scripts_error_logger.error("Ошибка при создании пользователя")
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при выполнении задачи: {error_message}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

@shared_task
def monitor_pipeline_task(run_id):
    try:
        if monitor_pipeline_completion(run_id):
            scripts_info_logger.info(f"Пайплайн с ID {run_id} успешно завершен.")
        else:
            scripts_error_logger.error(f"Возникли проблемы с пайплайном с ID {run_id}.")
    except PipelineStatusError as e:
        scripts_error_logger.error(f"Произошла ошибка при мониторинге пайплайна: {str(e)}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")


@shared_task
def add_user_nextcloud_task(client_name, account_name, group_name):
    try:
        scripts_info_logger.info(f"Запуск задачи по созданию нового пользователя {client_name} в NextCloud")
        NEXTCLOUD_URL = os.environ.get('NEXTCLOUD_URL')
        NEXTCLOUD_USER = os.environ.get('NEXTCLOUD_USER')
        NEXTCLOUD_PASSWORD = os.environ.get('NEXTCLOUD_PASSWORD')

        # Инициализация экземпляра NextCloud
        create_nextcloud_account = NextCloudManager(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)
        create_nextcloud_account.execute_all(client_name, account_name, group_name)
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при выполнении задачи: {error_message}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

@shared_task
def delete_user_nextcloud_task(account_name, group_name):
    try:
        scripts_info_logger.info(f"Запуск задачи по удалению пользователя {account_name} в NextCloud")
        NEXTCLOUD_URL = os.environ.get('NEXTCLOUD_URL')
        NEXTCLOUD_USER = os.environ.get('NEXTCLOUD_USER')
        NEXTCLOUD_PASSWORD = os.environ.get('NEXTCLOUD_PASSWORD')

        # Инициализация экземпляра NextCloud
        create_nextcloud_account = NextCloudManager(NEXTCLOUD_URL, NEXTCLOUD_USER, NEXTCLOUD_PASSWORD)
        create_nextcloud_account.execute_deletion(account_name, group_name)
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при выполнении задачи: {error_message}")
        scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
