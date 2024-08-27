import requests
import json
import uuid
import os
import smtplib
import logging
from jinja2 import Environment, FileSystemLoader
from logger.log_config import setup_logger, get_abs_log_path
from datetime import datetime
from dotenv import load_dotenv
from django.conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.utils import make_msgid
from scripts.confluence.get_info_release import get_server_release_notes, get_ipad_release_notes, get_android_release_notes
from scripts.yandex.yandexDocs import update_local_documentation


load_dotenv()

# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


# Создаем среду Jinja2
env = Environment(loader=FileSystemLoader(os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML')))

def render_template(template_name, context):
    template = env.get_template(template_name)
    return template.render(context)


def structure_updates_3x(updates):
    """
    Структурирует список обновлений в формате, пригодном для использования в шаблонизаторе.

    Функция принимает список строк, каждая из которых представляет собой отдельное обновление
    или заголовок модуля. Заголовки модулей отмечены специальными маркерами ("BoardMaps Core:" и "Модуль").
    
    Args:
        updates (list): Список строк с обновлениями и заголовками модулей.

    Returns:
        list: Список словарей, где каждый словарь представляет модуль и его обновления.
    """
    structured_updates = []  # Список для структурированных данных
    current_module = {"title": None, "updates": []}  # Текущий обрабатываемый модуль
    module_count = 1  # Счетчик модулей

    for update in updates:
        # Проверяем, является ли строка заголовком для "BoardMaps Core:"
        if 'BoardMaps Core:' in update:
            # Если в текущем модуле уже есть обновления, добавляем его в итоговый список
            if current_module["updates"]:
                structured_updates.append(current_module)
            # Начинаем новый модуль для "BoardMaps Core:"
            current_module = {"title": f"{module_count}. BoardMaps Core:", "updates": []}
            module_count += 1
        # Проверяем, является ли строка заголовком модуля
        elif 'Модуль' in update:
            # Если в текущем модуле уже есть обновления, добавляем его в итоговый список
            if current_module["updates"]:
                structured_updates.append(current_module)
            # Начинаем новый модуль
            current_module = {"title": f"{module_count}. {update.split(':')[0]}:", "updates": []}
            module_count += 1
        else:
            # Добавляем обновление в текущий модуль
            current_module["updates"].append(update)
    
    # Добавляем последний обработанный модуль в список, если в нем есть обновления
    if current_module["updates"]:
        structured_updates.append(current_module)

    return structured_updates


def send_test_email(version, emails, mobile_version=None, mailing_type='standard_mailing', additional_type=None):
    """
    Функция для тестовой отправки версии релиза.

    Args:
        version (str): Версия релиза.
        emails (list): Список адресатов электронной почты для отправки письма рассылки.
        mobile_version (str, optional): Версия мобильного приложения.
        mailing_type (str): Тип рассылки ('standard_mailing' или 'hotfix').
        additional_type (str, optional): Дополнительный тип (например, 'ipad' или 'android').
    """

    # Проверка входных данных
    if not version or not emails:
        error_message = "Ошибка: не указаны обязательные параметры (версия или адрес электронной почты)."
        scripts_error_logger.error(error_message)
        raise ValueError(error_message)

    # if mailing_type == 'standard_mailing' and version.startswith('3.') and not mobile_version:
    #     error_message = "Ошибка: для стандартной рассылки версии 3.x необходимо указать мобильную версию."
    #     scripts_error_logger.error(error_message)
    #     raise ValueError(error_message)

    try:
        # Указываем путь к файлу с данными
        CONFIG_FILE = "./Main.config"

        # Проверяем есть ли заполненный аргумент для мобильной версии
        if mobile_version is None:
            # Если не заполнен, тогда указываем как у сервера (для 2.х версий)
            mobile_version = version

        # Открываем файл и загружаем данные
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as json_file:
            DATA = json.load(json_file)
            MAIL_SETTINGS = DATA['MAIL_SETTINGS']
            CREG_URL = DATA['CREG']['URL']
            CREG_USERNAME = DATA['CREG']['USERNAME']
            CREG_PASSWORD = DATA['CREG']['PASSWORD']
            # Получаем значения токена для Яндекс.Диска и списка папок
            YANDEX_OAUTH_TOKEN = DATA["YANDEX_DISK"]["OAUTH-TOKEN"]
            YANDEX_DISK_FOLDERS = DATA["YANDEX_DISK_FOLDERS"]

        try:
            # Обновляем документацию перед отправкой письма
            updated_folder_paths = [folder_path.format(version_info=version) for folder_path in YANDEX_DISK_FOLDERS]
            update_local_documentation(YANDEX_OAUTH_TOKEN, version, updated_folder_paths)
        except requests.exceptions.RequestException as error:
            error_message = f"Ошибка запроса к Яндекс.Диску: {error}"
            scripts_error_logger.error(error_message)
            raise

        # Добавьте адрес электронной почты для скрытой копии
        bcc_email = MAIL_SETTINGS['FROM']

        # Преобразование списка адресов электронной почты в строку
        email_send = ", ".join(emails) if isinstance(emails, list) else emails

        # Создание письма
        msg = MIMEMultipart()
        msg['From'] = MAIL_SETTINGS['FROM']
        msg['To'] = email_send
        msg['Subject'] = Header(f'Обновление BoardMaps {version}', 'utf-8')

        # Добавление скрытой копии
        msg['Bcc'] = bcc_email

        # Запрос уведомления о доставке
        msg['Disposition-Notification-To'] = MAIL_SETTINGS['FROM']

        # Запрос уведомления о прочтении
        msg['Return-Receipt-To'] = MAIL_SETTINGS['FROM']
        msg['X-Confirm-Reading-To'] = MAIL_SETTINGS['FROM']
        msg['X-MS-Read-Receipt-To'] = MAIL_SETTINGS['FROM']

        # Создание Message-ID для отслеживания
        msg_id = make_msgid()
        msg['Message-ID'] = msg_id

        # Подготовка данных для шаблона
        server_updates = None
        ipad_updates = None
        android_updates = None

        # Выбор шаблона на основе версии, вида рассылки и дополнительного типа
        version_prefix = version.split('.')[0]
        
        if mailing_type == 'standard_mailing':
            if version_prefix == '2':
                server_updates = get_server_release_notes(version)
                ipad_updates = get_ipad_release_notes(mobile_version)
                android_updates = get_android_release_notes(mobile_version)
                template_file = 'index_2x.html'
            elif version_prefix == '3':
                server_updates = structure_updates_3x(get_server_release_notes(version))
                ipad_updates = get_ipad_release_notes(mobile_version)
                android_updates = get_android_release_notes(mobile_version)
                template_file = 'index_3x.html'
            else:
                # Обработка неподдерживаемой версии
                error_message = f"Для стандартной рассылки шаблон версии {version} не найден"
                scripts_error_logger.error(error_message)
                raise FileNotFoundError(error_message)
        elif mailing_type == 'hotfix':
            if additional_type == 'ipad':
                ipad_updates = get_ipad_release_notes(mobile_version)
                template_file = 'index_ipad.html'
            elif additional_type == 'android':
                android_updates = get_android_release_notes(mobile_version)
                template_file = 'index_android.html'
            else:
                if version_prefix == '2':
                    server_updates = get_server_release_notes(version)
                    template_file = 'index_2x_hotfix_server.html'
                elif version_prefix == '3':
                    server_updates = structure_updates_3x(get_server_release_notes(version))
                    template_file = 'index_3x_hotfix_server.html'
                else:
                    # Обработка неподдерживаемой версии
                    error_message = f"Для hotfix рассылки шаблон версии {version} не найден"
                    scripts_error_logger.error(error_message)
                    raise FileNotFoundError(error_message)
        else:
            # Обработка неподдерживаемой версии
            error_message = f"Шаблон для версии {version} не найден"
            scripts_error_logger.error(error_message)
            raise FileNotFoundError(error_message)

        context = {
            'number_version': version,
            'server_updates': server_updates,
            'ipad_updates': ipad_updates,
            'android_updates': android_updates
        }

        # Рендеринг HTML из шаблона
        html = render_template(template_file, context)

        # Генерация уникального идентификатора для каждого письма и добавление его в шаблон
        unique_id = uuid.uuid4()
        html += f'''
        <!-- Скрытый уникальный идентификатор письма: {unique_id} -->
        <div style="display:none;">ID письма: {unique_id}</div>
        '''
        
        # Добавление HTML шаблона в сообщение
        msg.attach(MIMEText(html, 'html'))

        # Добавление изображений для CID картинок в шаблоне HTML
        images_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'Images')
        for image in os.listdir(images_dir):
            image_path = os.path.join(images_dir, image)
            if os.path.isfile(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read(), name=os.path.basename(image))
                    img.add_header('Content-ID', '<{}>'.format(image))
                    msg.attach(img)

        # Вложение PDF файлов
        attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment')
        if os.path.isdir(attachments_dir):
            for attachment in os.listdir(attachments_dir):
                attachment_path = os.path.join(attachments_dir, attachment)
                if os.path.isfile(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                        msg.attach(part)

        # Отправка письма
        with smtplib.SMTP(MAIL_SETTINGS['SMTP'], 587) as server:
            server.starttls()
            server.login(MAIL_SETTINGS['USER'], MAIL_SETTINGS['PASSWORD'])
            server.send_message(msg)
            scripts_info_logger.info("Письмо было успешно отправлено на почту: %s", email_send)
            return True

        # Проверка наличия уведомлений о доставке и прочтении
        if 'Disposition-Notification-To' in msg and 'Return-Receipt-To' in msg:
            delivery_status = server.esmtp_features.get('8bitmime', False)
            read_receipt = server.esmtp_features.get('dsn', False)
            if delivery_status:
                print("Запросы уведомлений о доставке поддерживаются.")
            if read_receipt:
                print("Запросы уведомлений о прочтении поддерживаются.")

    except FileNotFoundError as error:
        scripts_error_logger.error('Файл не найден: %s', error.filename)
    except smtplib.SMTPException as error:
        scripts_error_logger.error('Ошибка при отправке письма через SMTP: %s', str(error))
    except Exception as error:
        scripts_error_logger.error('Неизвестная ошибка при отправке письма: %s', str(error))
    return False
