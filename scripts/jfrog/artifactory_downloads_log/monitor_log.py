import os
import re
import json
import emoji
import logging
from logger.log_config import setup_logger, get_abs_log_path
from django.db import transaction
from datetime import datetime, timedelta
from django.conf import settings
from scripts.telegram.send_message import Alert
import pytz
from main.models import ClientsCard, TechInformationCard, ReportDownloadjFrog
from django.core.exceptions import ValidationError


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


# Создаем объект класса Alert
alert = Alert()

# Указываем путь к файлу с данными
CONFIG_FILE = os.path.join(settings.BASE_DIR, "Main.config")

if os.getenv('GITHUB_ACTIONS') == 'true':
    DATA = "mocked configuration"
else:
    # Читаем данные из файла
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
        DATA = json.load(file)

# Получаем значение ключа GROUP_SUPPOR_TEAM в SEND_ALERT
GROUP_SUPPOR_TEAM = DATA['SEND_ALERT']['GROUP_SUPPOR_TEAM']

utc = pytz.UTC

def update_client_and_report(log_date, ip_address, account_name, image_name, version):
    try:
        with transaction.atomic():
            # Проверяем наличие записи в БД, чтобы избежать дублирования
            existing_report = ReportDownloadjFrog.objects.filter(
                date=log_date,
                account_name=account_name,
                image_name=image_name,
                version_download=version
            ).exists()

            if existing_report:
                scripts_info_logger.info(f"Запись для клиента {account_name} с образом {image_name} версии {version} уже существует. Пропускаем.")
                return

            # Запись в таблицу отчетов
            report = ReportDownloadjFrog(
                date=log_date,
                account_name=account_name,
                image_name=image_name,
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

            # Получаем имя клиента для отправки в сообщении
            client_name = client_card.client_info.client_name

            scripts_info_logger.info(f'Клиент: {client_name} был успешно добавлен в БД, Версии скачивания: {version}')

            # Формируем сообщение в телеграм-бот
            info_download_jfrog_message = (
                f"{emoji.emojize(':alien:')} <b>{client_name}</b>\n"
                f"{emoji.emojize(':mage:')} скачал образ {image_name}\n"
                f"{emoji.emojize(':dna:')} версии {version}\n"
                f"{emoji.emojize(':frog:')} из репозитория jFrog.\n"
            )

            # Отправляем алерт в группу саппорта
            alert.send_telegram_message(GROUP_SUPPOR_TEAM, info_download_jfrog_message)

    except ClientsCard.DoesNotExist:
        if account_name not in ["non_authenticated_user", "svc"]:
            scripts_error_logger.error(f"Клиент с short_name {account_name} не существует.")
    except ValidationError as error_message:
        scripts_error_logger.error(f"Ошибка валидации данных: {error_message}")
    except ValueError as error_message:
        scripts_error_logger.error(f"Неверный формат данных: {error_message}")
    except Exception as error_message:
        scripts_error_logger.error(f"Общая ошибка: {error_message}")


def analyze_logs_and_update_db():
    log_file_path = os.path.join(settings.BASE_DIR, "scripts/jfrog/artifactory_downloads_log/log/artifactory-request.log")

    if not os.path.exists(log_file_path) or not os.access(log_file_path, os.R_OK):
        scripts_error_logger.error("Файл журнала не существует или недоступен для чтения")
        # Проверяем, что директория существует, и выводим содержимое
        log_dir = os.path.dirname(log_file_path)
        if os.path.exists(log_dir):
            scripts_info_logger.info(f"Содержимое директории {log_dir}: {os.listdir(log_dir)}")
        else:
            scripts_info_logger.error(f"Директория {log_dir} не существует")
        return

    # Регулярное выражение для поиска нужной информации в логах
    pattern = re.compile(r"(\S{24})\|.*?(\S+)\|(\S+)\|(\S+)\|HEAD\|/api/docker/public/v2/([\w-]+)/manifests/([\d.]+)")

    # Устанавливаем диапазон времени для последних 4 часов
    current_date = datetime.now().replace(tzinfo=utc)
    two_hours_ago = (current_date - timedelta(hours=4)).replace(tzinfo=utc)
    
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                match = pattern.match(line)
                if match:
                    # Извлекаем дату из лога и преобразовываем её в объект datetime
                    log_date_str = match.group(1)
                    if log_date_str:
                        log_date = datetime.fromisoformat(log_date_str.replace("Z", "+00:00"))  # убираем 'Z', так как это UTC

                        # Проверяем, находится ли дата лога в диапазоне последних двух часов
                        if log_date >= two_hours_ago:
                            ip_address = match.group(3)
                            account_name = match.group(4)
                            image_name = match.group(5)
                            version = match.group(6)
                            # scripts_info_logger.info(f'Учётная запись: {account_name}, Образ: {image_name}, Версии: {version}')

                            # Находим клиента и обновляем информацию
                            update_client_and_report(log_date, ip_address, account_name, image_name, version)

    except IOError as error_message:
        scripts_error_logger.error(f"Не удалось прочитать файл: {error_message}")


def analyze_logs_and_get_data():
    log_file_path = os.path.join(settings.BASE_DIR, "scripts/jfrog/artifactory_downloads_log/log/artifactory-request.log")

    if not os.path.exists(log_file_path) or not os.access(log_file_path, os.R_OK):
        scripts_error_logger.error("Файл журнала не существует или недоступен для чтения")
        # Проверяем, что директория существует, и выводим содержимое
        log_dir = os.path.dirname(log_file_path)
        if os.path.exists(log_dir):
            scripts_info_logger.info(f"Содержимое директории {log_dir}: {os.listdir(log_dir)}")
        else:
            scripts_error_logger.error(f"Директория {log_dir} не существует")
        return "Ошибка файла журнала логов jFrog", []

    pattern = re.compile(r"(\S{24})\|.*?(\S+)\|(\S+)\|(\S+)\|HEAD\|/api/docker/public/v2/([\w-]+)/manifests/([\d.]+)")

    client_data_list = []
    
    current_date = datetime.now().replace(tzinfo=utc)
    two_days_ago = (current_date - timedelta(days=2)).replace(tzinfo=utc)
    
    with open(log_file_path, 'r') as file:
        for line in file:
            match = pattern.search(line) # Ищем строку через search по регулярке
            if match:
                log_date_str = match.group(1)
                if log_date_str:
                    log_date = datetime.fromisoformat(log_date_str.replace("Z", "+00:00")) # Преобразование времени в формат с учетом UTC
                    
                    if log_date >= two_days_ago:
                        scripts_info_logger.info(f'Строка подходит под регулярку: {match.group()}')
                        ip_address = match.group(3)
                        account_name = match.group(4)
                        image_name = match.group(5)
                        version = match.group(6)
                        scripts_info_logger.info(f'Учётная запись: {account_name}, Образ: {image_name}, Версии: {version}')
                        client_data_list.append({"account_name": account_name, "image_name": image_name, "version": version, "log_date": log_date, "ip_address": ip_address})
                    
    return "Успешно", client_data_list
