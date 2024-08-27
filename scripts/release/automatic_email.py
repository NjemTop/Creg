from main.models import ReleaseInfo, ClientsList, ContactsCard, TechInformationCard
from .test_automatic_email import send_test_email
from django.utils import timezone
import os
import logging
from logger.log_config import setup_logger, get_abs_log_path
from dotenv import load_dotenv


load_dotenv()

# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


def get_clients_for_mailing(version_prefix):
    """
    Получает словарь активных клиентов и их контактов для рассылки на основе версии продукта.
    
    Args:
        version_prefix (str): Префикс версии продукта ("2" или "3").
        
    Returns:
        dict: Словарь, где ключ - ID клиента, значение - список его контактов для рассылки.
    """
    try:
        clients_for_mailing = {}
        # Получаем активных клиентов из базы данных
        active_clients = ClientsList.objects.filter(contact_status=True)

        # Определяем ID клиентов с указанной версией продукта
        client_ids_for_version = TechInformationCard.objects.filter(
            server_version__startswith=version_prefix,
            client_card__client_info__in=active_clients
        ).values_list('client_card__client_info_id', flat=True)

        # Для каждого клиента собираем список контактов, которым нужно отправить рассылку
        for client_id in client_ids_for_version:
            contacts = ContactsCard.objects.filter(
                client_card__client_info_id=client_id,
                notification_update_new=True
            ).values_list('contact_email', flat=True)
            
            if contacts:
                clients_for_mailing[client_id] = list(contacts)
        
        scripts_info_logger.info(f"Найдено {len(clients_for_mailing)} клиентов для рассылки.")
        return clients_for_mailing
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при получении списка клиентов для рассылки: {error_message}")
        return {}


def send_mailing(version, mobile_version=None, mailing_type='standard_mailing', additional_type=None):
    """
    Отправляет рассылку клиентам в зависимости от версии продукта.

    Args:
        version (str): Версия релиза для рассылки.
        mobile_version (str, optional): Версия мобильного приложения. Необязательно.
        mailing_type (str): Тип рассылки ('standard_mailing' или 'hotfix').
        additional_type (str, optional): Дополнительный тип рассылки (например, 'ipad' или 'android').

    Рассылка происходит только для клиентов с активным статусом и подписанных на рассылку.
    Для каждого контакта рассылки создается запись в таблице ReleaseInfo.
    """
    
    # Получение словаря клиентов и их контактов для рассылки
    clients_contacts = get_clients_for_mailing(version.split('.')[0])

    # Проверка на наличие контактов для рассылки
    if not clients_contacts:
        scripts_error_logger.error(f"Нет контактов для отправки рассылки версии {version}.")
        return

    scripts_info_logger.info(f"Рассылка для версии {version} началась...")

    # Перебор каждого клиента и его контактов для отправки рассылки
    for client_id, emails in clients_contacts.items():
        try:
            # Получение объекта клиента по ID
            client = ClientsList.objects.get(pk=client_id)
            client_name = client.client_name

            # Проверка, была ли рассылка отправлена этому клиенту
            if ReleaseInfo.objects.filter(release_number=version, client_name=client_name).exists():
                scripts_info_logger.info(f"Рассылка версии {version} уже была отправлена клиенту {client_name}. Пропуск.")
                continue

            # Попытка отправки письма и проверка ее успешности
            if send_test_email(version, emails, mobile_version, mailing_type=mailing_type, additional_type=additional_type):
                # Запись об успешной отправке рассылки
                ReleaseInfo.objects.create(
                    date=timezone.now().date(),
                    release_number=version,
                    client_name=client_name,
                    client_email=emails
                )
                scripts_info_logger.info(f"Рассылка клиенту {client_name} (версия {version}) успешно выполнена для контактов: {emails}.")
            else:
                scripts_error_logger.error(f"Ошибка при отправке рассылки клиенту {client_name} (версия {version}).")
        except Exception as error_message:
            scripts_error_logger.error(f"Ошибка в процессе рассылки версии {version}: {str(error_message)}")

    scripts_info_logger.info(f"Рассылка для версии {version} успешно завершена.")
