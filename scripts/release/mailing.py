import requests
import json
import uuid
import os
import shutil
import smtplib
import logging
from main.models import ReleaseInfo, ClientsList, ContactsCard, TechInformationCard
from jinja2 import Environment, FileSystemLoader
from logger.log_config import setup_logger, get_abs_log_path, log_errors
from datetime import datetime
from retrying import retry
from dotenv import load_dotenv
from django.conf import settings
from django.utils import timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.utils import make_msgid
from scripts.email.settings import set_email_config
from scripts.confluence.get_info_release import get_server_release_notes, get_ipad_release_notes, get_android_release_notes
from scripts.yandex.yandex_docs import download_and_upload_pdf_files, update_local_documentation
# from scripts.yandex.DistrMoveFromShare import move_distr_and_manage_share
# from scripts.yandex.SkinMoveFromShare import move_skins_and_manage_share


load_dotenv()

# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


def send_email_extra_info(*args, **kwargs):
    error = kwargs.get('error')
    if isinstance(error, FileNotFoundError):
        return f"Файл не найден: {error.filename}"
    elif isinstance(error, smtplib.SMTPException):
        return f"Ошибка при отправке письма через SMTP: {str(error)}"
    elif isinstance(error, ValueError):
        return f"Неверное значение: {str(error)}"
    elif isinstance(error, KeyError):
        return f"Ключ не найден: {str(error)}"
    return "Неизвестная ошибка при отправке письма"


class EmailSender:
    """
    Класс для отправки электронной почты с обновлениями.

    Атрибуты:
        emails (list): Список адресов электронной почты получателей.
        mailing_type (str): Тип рассылки ('standard_mailing' или 'hotfix').
        release_type (str): Тип релиза (например, 'release3x' или 'releaseAndroid3x').
        server_version (str, optional): Версия серверной части релиза.
        ipad_version (str): Версия мобильного приложения для iPad/iOS.
        android_version (str): Версия мобильного приложения для Android.
        language (str): Язык клиента ('ru' или 'en').

    Методы:
        send_email(): Отправляет электронное письмо.
    """

    def __init__(self, emails, mailing_type, release_type, server_version=None, ipad_version=None, android_version=None, language='ru'):
        """
        Инициализирует объект EmailSender.

        Args:
            emails (list or str): Адреса электронной почты получателей.
            mailing_type (str): Тип рассылки ('standard_mailing' или 'hotfix').
            release_type (str): Тип релиза (например, 'release3x' или 'releaseAndroid3x').
            server_version (str, optional): Версия серверной части релиза.
            ipad_version (str, optional): Версия мобильного приложения для iPad/iOS.
            android_version (str, optional): Версия мобильного приложения для Android.
            language (str): Язык клиента ('ru' или 'en').
        """
        self.server_version = server_version
        self.emails = emails if isinstance(emails, list) else [emails]
        self.mailing_type = mailing_type
        self.release_type = release_type
        self.ipad_version = ipad_version if ipad_version is not None else ''
        self.android_version = android_version if android_version is not None else ''
        self.language = language
        self.logger = scripts_info_logger
        self.error_logger = scripts_error_logger
        self.config = self._load_config()
        self.env = Environment(loader=FileSystemLoader(os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML')))
        self.msg = MIMEMultipart()

    @log_errors()
    def _load_config(self):
        """
        Загружает конфигурацию из файла.

        Returns:
            dict: Содержимое конфигурационного файла.
        """
        CONFIG_FILE = "./Main.config"
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as json_file:
            return json.load(json_file)

    def _structure_updates_3x(self, updates):
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

    def _get_template_name(self):
        """
        Возвращает имя шаблона на основе версии, вида рассылки и группы релиза.

        Returns:
            str: Имя шаблона.

        Raises:
            FileNotFoundError: Если шаблон не найден.
        """
        language_suffix = f'_{self.language}'

        # Логика для стандартной рассылки
        if self.mailing_type == 'standard_mailing':
            if self.release_type == 'release2x':
                return f'index_2x{language_suffix}.html'
            elif self.release_type == 'release3x':
                return f'index_3x{language_suffix}.html'

        # Логика для рассылки хотфиксов
        elif self.mailing_type == 'hotfix':
            if self.release_type == 'release2x':
                return f'index_2x_hotfix_server{language_suffix}.html'
            elif self.release_type == 'release3x':
                return f'index_3x_hotfix_server{language_suffix}.html'
            elif self.release_type == 'releaseAndroid2x':
                return f'index_2x_hotfix_android{language_suffix}.html'
            elif self.release_type == 'releaseAndroid3x':
                return f'index_3x_hotfix_android{language_suffix}.html'
            elif self.release_type == 'releaseiPad2x':
                return f'index_2x_hotfix_ipad{language_suffix}.html'
            elif self.release_type == 'releaseiPad3x':
                return f'index_3x_hotfix_ipad{language_suffix}.html'
            elif self.release_type == 'releaseModule':
                return f'index_module_hotfix{language_suffix}.html'
            elif self.release_type == 'releaseIntegration':
                return f'index_integration_hotfix{language_suffix}.html'

        raise FileNotFoundError(f"Шаблон для версии {self.server_version}, типа {self.release_type} и языка {self.language} не найден")

    def _prepare_context(self):
        """
        Подготавливает контекст для рендеринга шаблона.

        Returns:
            dict: Контекст с обновлениями.
        """
        context = {
            'number_version': self.server_version,
            'server_updates': None,
            'ipad_updates': None,
            'android_updates': None
        }

        language_mapping = {
            'ru': 'Русский',
            'en': 'Английский'
        }

        try:
            lang_key = language_mapping.get(self.language, 'Русский')  # Используем 'Русский' по умолчанию

            if self.mailing_type == 'standard_mailing':
                server_notes = get_server_release_notes(self.server_version)
                self.logger.info(f"Полученные данные обновлений сервера: {server_notes}")

                if self.release_type == 'release3x':
                    context['server_updates'] = self._structure_updates_3x(server_notes.get(lang_key, []))
                else:
                    context['server_updates'] = server_notes.get(lang_key, [])

                if self.ipad_version:
                    ipad_notes = get_ipad_release_notes(self.ipad_version)
                    self.logger.info(f"Полученные данные обновлений iPad: {ipad_notes}")
                    context['ipad_updates'] = ipad_notes.get(lang_key, [])

                if self.android_version:
                    android_notes = get_android_release_notes(self.android_version)
                    self.logger.info(f"Полученные данные обновлений Android: {android_notes}")
                    context['android_updates'] = android_notes.get(lang_key, [])

            elif self.mailing_type == 'hotfix':
                if self.release_type in ['release2x', 'release3x']:
                    server_notes = get_server_release_notes(self.server_version)
                    self.logger.info(f"Полученные данные обновлений сервера: {server_notes}")
                    if self.release_type == 'release3x':
                        context['server_updates'] = self._structure_updates_3x(server_notes.get(lang_key, []))
                    else:
                        context['server_updates'] = server_notes.get(lang_key, [])

                if self.release_type in ['releaseAndroid2x', 'releaseAndroid3x'] and self.android_version:
                    android_notes = get_android_release_notes(self.android_version)
                    self.logger.info(f"Полученные данные обновлений Android: {android_notes}")
                    context['android_updates'] = android_notes.get(lang_key, [])

                if self.release_type in ['releaseiPad2x', 'releaseiPad3x'] and self.ipad_version:
                    ipad_notes = get_ipad_release_notes(self.ipad_version)
                    self.logger.info(f"Полученные данные обновлений iPad: {ipad_notes}")
                    context['ipad_updates'] = ipad_notes.get(lang_key, [])

        except KeyError as key_error:
            self.error_logger.error(f"Ошибка при подготовке контекста: ключ {key_error} не найден в данных обновления.")
            raise
        except Exception as error_message:
            self.error_logger.error(f"Ошибка при подготовке контекста: {str(error_message)}")
            raise

        return context


    def _render_html(self, template_name, context):
        """
        Рендерит HTML из шаблона и контекста.

        Args:
            template_name (str): Имя шаблона.
            context (dict): Контекст для рендеринга.

        Returns:
            str: Отрендеренный HTML.
        """
        try:
            template = self.env.get_template(template_name)
            html = template.render(context)
            unique_id = uuid.uuid4()
            html += f'<!-- Скрытый уникальный идентификатор письма: {unique_id} -->'
            html += f'<div style="display:none;">ID письма: {unique_id}</div>'
            return html
        except Exception as e:
            self.error_logger.error(f"Ошибка при рендеринге HTML: {str(e)}")
            raise

    def _attach_html(self, html):
        """
        Присоединяет HTML к сообщению.

        Args:
            html (str): HTML для присоединения.
        """
        self.msg.attach(MIMEText(html, 'html'))

    def _attach_images(self):
        """
        Присоединяет изображения к сообщению.
        """
        images_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'Images')
        for image in os.listdir(images_dir):
            image_path = os.path.join(images_dir, image)
            if os.path.isfile(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read(), name=os.path.basename(image))
                    img.add_header('Content-ID', '<{}>'.format(image))
                    self.msg.attach(img)
                    self.logger.info(f"Изображение {image} успешно прикреплено.")
            else:
                self.logger.error(f"Изображение {image} не найдено по пути {image_path}.")

    def _attach_files(self):
        """
        Присоединяет файлы к сообщению из заранее скачанной локальной директории.
        """
        attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', self.language.upper())
        files_attached = False
        if os.path.isdir(attachments_dir):
            for attachment in os.listdir(attachments_dir):
                attachment_path = os.path.join(attachments_dir, attachment)
                if os.path.isfile(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                        self.msg.attach(part)
                        self.logger.info(f"Файл {attachment} успешно прикреплен.")
                        files_attached = True
                else:
                    self.logger.error(f"Файл {attachment} не найден по пути {attachment_path}.")

        if not files_attached:
            self.logger.error("Ни один файл не был найден для прикрепления.")

    def update_documentation(self):
        """
        Обновляет документацию перед отправкой письма. Скачивает её только если она еще не скачана для текущего языка.
        """
        yandex_token = self.config["YANDEX_DISK"]["OAUTH-TOKEN"]
        yandex_folders = self.config["YANDEX_DISK_FOLDERS"]

        # Определяем директорию для хранения документов по языку
        attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', self.language.upper())

        try:
            if not os.path.exists(attachments_dir):
                os.makedirs(attachments_dir)
                scripts_info_logger.info(f"Создана директория для документации: {attachments_dir}")
        except OSError as error_message:
            scripts_info_logger.error(f"Ошибка при создании директории {attachments_dir}: {str(error_message)}")
            raise

        # Проверяем, есть ли уже скачанные документы
        if not os.listdir(attachments_dir):
            scripts_info_logger.info(f"Документация для языка {self.language.upper()} и версии {self.server_version} не найдена локально, начинается скачивание...")
            update_local_documentation(yandex_token, yandex_folders, self.release_type, self.language, self.server_version, self.ipad_version, self.android_version)
        else:
            scripts_info_logger.info(f"Документация для языка {self.language.upper()} и версии {self.server_version} уже скачана, повторное скачивание не требуется.")

    def _get_subject(self):
        """
        Возвращает тему письма на основе языка.

        Returns:
            str: Тема письма.
        """
        version_to_use = self.server_version or self.android_version or self.ipad_version
        if not version_to_use:
            raise ValueError("Не указан ни один номер версии (ни сервер, ни мобильное приложение).")

        subjects = {
            'ru': f'Обновление BoardMaps {version_to_use}',
            'en': f'BoardMaps Update {version_to_use}'
        }
        return subjects.get(self.language, subjects['ru'])

    @retry(stop_max_attempt_number=5, wait_fixed=10000)
    @log_errors(extra_info=send_email_extra_info)
    def send_email(self):
        """
        Отправляет электронное письмо.

        Returns:
            bool: True, если письмо было успешно отправлено, иначе False.
        """
        mail_settings = self.config['MAIL_SETTINGS']
        email_send = ", ".join(self.emails)
        self.msg['From'] = mail_settings['FROM']
        self.msg['To'] = email_send
        self.msg['Subject'] = Header(self._get_subject(), 'utf-8')
        self.msg['Bcc'] = mail_settings['FROM']
        self.msg['Disposition-Notification-To'] = mail_settings['FROM']
        self.msg['Return-Receipt-To'] = mail_settings['FROM']
        self.msg['X-Confirm-Reading-To'] = mail_settings['FROM']
        self.msg['X-MS-Read-Receipt-To'] = mail_settings['FROM']
        self.msg['Message-ID'] = make_msgid()

        # Обновляем документацию перед отправкой письма
        self.update_documentation()

        template_name = self._get_template_name()
        context = self._prepare_context()
        html = self._render_html(template_name, context)
        self._attach_html(html)
        self._attach_images()
        self._attach_files()

        with smtplib.SMTP(mail_settings['SMTP'], 587) as server:
            server.starttls()
            server.login(mail_settings['USER'], mail_settings['PASSWORD'])
            server.send_message(self.msg)
            self.logger.info(f"Письмо было успешно отправлено на почту: {email_send}")
            return True

def send_test_email(emails, mailing_type, release_type, server_version=None, ipad_version=None, android_version=None, language='ru'):
    """
    Функция для тестовой отправки версии релиза.

    Args:
        emails (list): Список адресатов электронной почты для отправки письма рассылки.
        mailing_type (str): Тип рассылки ('standard_mailing' или 'hotfix').
        release_type (str): Тип релиза (например, 'release3x' или 'releaseAndroid3x').
        server_version (str, optional): Версия серверной части релиза.
        ipad_version (str, optional): Версия мобильного приложения для iPad/iOS.
        android_version (str, optional): Версия мобильного приложения для Android.
        language (str): Язык клиента ('ru' или 'en').

    Returns:
        bool: True, если письмо было успешно отправлено, иначе False.
    """
    clear_attachments_directory()  # Очищаем папку с вложениями перед началом

    sender = EmailSender(emails, mailing_type, release_type, server_version, ipad_version, android_version, language)
    return sender.send_email()

@log_errors()
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
                notification_update=True
            ).values_list('contact_email', flat=True)
            
            if contacts:
                clients_for_mailing[client_id] = list(contacts)
        
        scripts_info_logger.info(f"Найдено {len(clients_for_mailing)} клиентов для рассылки.")
        return clients_for_mailing
    except Exception as error_message:
        scripts_error_logger.error(f"Ошибка при получении списка клиентов для рассылки: {error_message}")
        return {}

def clear_attachments_directory():
    """
    Очищает папку с вложениями перед началом новой рассылки.
    """
    attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment')

    # Удаление старых документов из папки
    if os.path.isdir(attachments_dir):
        for item in os.listdir(attachments_dir):
            item_path = os.path.join(attachments_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    scripts_info_logger.info(f"Удален файл: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    scripts_info_logger.info(f"Удалена папка: {item_path}")
            except Exception as error_message:
                scripts_error_logger.error(f"Ошибка при удалении {item_path}: {str(error_message)}")

@log_errors()
def send_mailing(mailing_type, release_type, server_version=None, ipad_version=None, android_version=None):
    """
    Основная функция для отправки рассылки клиентам.

    Args:
        mailing_type (str): Тип рассылки ('standard_mailing' или 'hotfix').
        release_type (str): Тип релиза (например, 'release3x' или 'releaseAndroid3x').
        server_version (str, optional): Версия серверной части релиза.
        ipad_version (str, optional): Версия iPad приложения. Необязательно.
        android_version (str, optional): Версия Android приложения. Необязательно.

    Returns:
        str: Сообщение о статусе рассылки.
    """
    clear_attachments_directory()  # Очищаем папку с вложениями перед началом

    sender = EmailSender(None, mailing_type, release_type, server_version, ipad_version, android_version)
    # Получение контактов клиентов для рассылки
    clients_contacts = get_clients_for_mailing(server_version.split('.')[0])

    if not clients_contacts:
        scripts_error_logger.error(f"Нет контактов для отправки рассылки версии {server_version}.")
        return 'Нет контактов для отправки рассылки.'

    scripts_info_logger.info(f"Рассылка для версии {server_version} началась...")

    # Подготовка данных для рассылки
    nextcloud_settings = sender.config['NEXT_CLOUD']
    nextcloud_url = nextcloud_settings['URL']
    nextcloud_username = nextcloud_settings['USER']
    nextcloud_password = nextcloud_settings['PASSWORD']

    # Скачивание и загрузка документации на Nextcloud
    download_and_upload_pdf_files(
        sender.config["YANDEX_DISK"]["OAUTH-TOKEN"], 
        nextcloud_url,
        nextcloud_username, 
        nextcloud_password, 
        sender.config["YANDEX_DISK_FOLDERS"],
        release_type,
        server_version,
        ipad_version,
        android_version
    )

    # Подготовка данных для рассылки
    successful_count, failed_count = send_mailing_to_clients(sender, mailing_type, release_type, server_version, ipad_version, android_version, clients_contacts)

    if successful_count == 0:
        scripts_error_logger.error(f"Ошибка: не удалось отправить ни одного письма для версии {server_version}.")
        return 'Ошибка: не удалось отправить ни одного письма.'
    elif failed_count > 0:
        scripts_error_logger.warning(f"Рассылка для версии {server_version} завершена с ошибками. Успешно: {successful_count}, Неудачно: {failed_count}.")
        return f'Предупреждение: Рассылка завершена с ошибками. Успешно: {successful_count}, Неудачно: {failed_count}.'
    else:
        scripts_info_logger.info(f"Рассылка для версии {server_version} успешно завершена.")
        return 'Рассылка успешно завершена.'

@log_errors()
def send_mailing_to_clients(sender, mailing_type, release_type, server_version, ipad_version, android_version, clients_contacts):
    """
    Отправляет письма клиентам с подготовленными данными.

    Args:
        mailing_type (str): Тип рассылки.
        release_type (str): Тип релиза (например, 'release3x' или 'releaseAndroid3x').
        server_version (str, optional): Версия серверной части релиза.
        ipad_version (str): Версия iPad приложения.
        android_version (str): Версия Android приложения.
        clients_contacts (dict): Словарь с клиентами и их контактами.

    Returns:
        tuple: Кортеж из двух элементов: количество успешных отправок и количество неуспешных отправок.
    """
    successful_count = 0
    failed_count = 0

    try:
        mail_settings = sender.config['MAIL_SETTINGS_SUPPORT']
        with smtplib.SMTP(mail_settings['SMTP'], 587) as server:
            server.starttls()
            server.login(mail_settings['USER'], mail_settings['PASSWORD'])

            for client_id, emails in clients_contacts.items():
                try:
                    client = ClientsList.objects.get(pk=client_id)
                    client_name = client.client_name
                    client_language = client.language

                    if ReleaseInfo.objects.filter(release_number=server_version, client_name=client_name).exists():
                        scripts_info_logger.info(f"Рассылка версии {server_version} уже была отправлена клиенту {client_name}. Пропуск.")
                        continue

                    # Используем переданный экземпляр sender
                    sender.emails = emails
                    sender.language = client_language

                    # Подготавливаем шаблон для каждого клиента
                    template_name = sender._get_template_name()
                    context = sender._prepare_context()
                    html = sender._render_html(template_name, context)

                    # Установим заголовки для каждого клиента
                    sender.msg['To'] = ", ".join(emails)
                    sender.msg['Subject'] = Header(sender._get_subject(), 'utf-8')
                    sender.msg['Bcc'] = mail_settings['FROM']
                    sender.msg.attach(MIMEText(html, 'html'))
                    
                    sender._attach_images()

                    # Обновляем документацию перед отправкой письма
                    sender.update_documentation()

                    sender._attach_files()

                    server.send_message(sender.msg)
                    scripts_info_logger.info(f"Письмо было успешно отправлено на почту: {emails}")

                    ReleaseInfo.objects.create(
                        date=timezone.now().date(),
                        release_number=server_version,
                        client_name=client_name,
                        client_email=emails
                    )
                    scripts_info_logger.info(f"Рассылка клиенту {client_name} (версия {server_version}) успешно выполнена для контактов: {emails}.")
                    successful_count += 1
                except Exception as error_message:
                    scripts_error_logger.error(f"Ошибка в процессе рассылки версии {server_version} клиенту {client_name}: {str(error_message)}")
                    failed_count += 1
    except Exception as e:
        scripts_error_logger.error(f"Ошибка при установке соединения с SMTP-сервером: {str(e)}")
        failed_count = len(clients_contacts)

    return successful_count, failed_count
