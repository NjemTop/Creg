import os
import re
import logging
from logger.log_config import setup_logger, get_abs_log_path
from django.db import transaction
from datetime import datetime, timedelta
from django.conf import settings
import pytz
from main.models import ClientsCard, TechInformationCard, ReportDownloadjFrog
from django.core.exceptions import ValidationError


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


utc = pytz.UTC

def update_client_and_report(log_date, ip_address, account_name, version):
    try:
        with transaction.atomic():

            # Запись в таблицу отчетов
            report = ReportDownloadjFrog(
                date=log_date,
                account_name=account_name,
                version_download=version,
                ip_address=ip_address
            )
            report.full_clean()  # Валидация модели
            report.save()

            # Поиск клиента по имени
            client_card = ClientsCard.objects.get(client_info__short_name=account_name)

            if not account_name or not version:
                raise ValueError("Неверные данные")

            # Обновляем информацию о версии в связанной таблице
            tech_info = client_card.tech_information
            tech_info.server_version = version
            tech_info.full_clean()  # Валидация модели
            tech_info.save()
            scripts_info_logger.info(f'Клиент: {account_name} был успешно добавлен в БД, Версии скачивания: {version}')

    except ClientsCard.DoesNotExist:
        scripts_error_logger.error(f"Клиент с short_name {account_name} не существует.")
    except ValidationError as error_message:
        scripts_error_logger.error(f"Ошибка валидации данных: {error_message}")
    except ValueError as error_message:
        scripts_error_logger.error(f"Неверный формат данных: {error_message}")
    except Exception as error_message:
        scripts_error_logger.error(f"Общая ошибка: {error_message}")


def analyze_logs_and_update_db():
    log_file_path = os.path.join(settings.BASE_DIR, "scripts/artifactory_downloads_log/log/artifactory-request.log")
    if not os.path.exists(log_file_path) or not os.access(log_file_path, os.R_OK):
        scripts_error_logger.error("Файл журнала не существует или недоступен для чтения")
        return

    # Регулярное выражение для поиска нужной информации в логах
    pattern = re.compile(r"(\S{24})\|.*?(\S+)\|(\S+)\|(\S+)\|HEAD\|/api/docker/public/v2/[\w-]+/manifests/([\d.]+)")

    # Устанавливаем текущую дату и дату два дня назад
    current_date = datetime.now().replace(tzinfo=utc)
    two_days_ago = (current_date - timedelta(days=2)).replace(tzinfo=utc)
    
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                match = pattern.match(line)
                if match:
                    # Извлекаем дату из лога и преобразовываем её в объект datetime
                    log_date_str = match.group(1)
                    if log_date_str:
                        log_date = datetime.fromisoformat(log_date_str.replace("Z", "+00:00"))  # убираем 'Z', так как это UTC

                        # Проверяем, находится ли дата лога в диапазоне последних двух дней
                        if log_date >= two_days_ago:
                            ip_address = match.group(3)
                            account_name, version = match.group(4), match.group(5)
                            scripts_info_logger.info(f'УЗ: {account_name}, Версии: {version}')

                            # Находим клиента и обновляем информацию
                            update_client_and_report(log_date, ip_address, account_name, version)

    except IOError as error_message:
        scripts_error_logger.error(f"Не удалось прочитать файл: {error_message}")


def analyze_logs_and_get_data():
    log_file_path = os.path.abspath("./scripts/artifactory_downloads_log/log/artifactory-request.log")
    if not os.path.exists(log_file_path):
        return "Файл журнала не существует", []

    pattern = re.compile(r"(\S{24})\|.*?(\S+)\|(\S+)\|(\S+)\|HEAD\|/api/docker/public/v2/[\w-]+/manifests/([\d.]+)")

    client_data_list = []
    
    current_date = datetime.now().replace(tzinfo=utc)
    two_days_ago = (current_date - timedelta(days=2)).replace(tzinfo=utc)
    
    with open(log_file_path, 'r') as file:
        for line in file:
            match = pattern.search(line) # Ищем строку через search по регулярке
            if match:
                scripts_info_logger.info(f'Строка подходит под регулярку: {match.group()}')
                log_date_str = match.group(1)
                if log_date_str:
                    log_date = datetime.fromisoformat(log_date_str.replace("Z", "+00:00")) # Преобразование времени в формат с учетом UTC
                    scripts_info_logger.info(f'Дата этой строки: {log_date}')
                    
                    if log_date >= two_days_ago:
                        ip_address = match.group(3)
                        account_name = match.group(4)
                        version = match.group(5)
                        scripts_info_logger.info(f'УЗ: {account_name}, Версии: {version}')
                        client_data_list.append({"account_name": account_name, "version": version, "log_date": log_date, "ip_address": ip_address})
                    
    return "Успешно", client_data_list
