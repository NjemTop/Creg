import os
import json
import uuid
from jinja2 import Environment, FileSystemLoader
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import make_msgid
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPException
from retrying import retry
from django.conf import settings

from apps.mailings.services.utils.retry_and_logging import log_errors
from apps.mailings.services.utils.attachments import (
    attach_images,
    attach_files,
    update_documentation,
    embed_hidden_logo,
)
from apps.mailings.services.base.helpers import log_updates
from apps.mailings.services.integrations.confluence import (
    get_server_release_notes,
    get_ipad_release_notes,
    get_android_release_notes,
)
from apps.mailings.services.utils.config import get_config_path
from apps.configurations.config_loader import get_integration_settings

# logging
import logging

logger = logging.getLogger(__name__)


def send_email_extra_info(*args, **kwargs):
    error = kwargs.get('error')
    if isinstance(error, FileNotFoundError):
        return f"Файл не найден: {error.filename}"
    elif isinstance(error, SMTPException):
        return f"Ошибка при отправке письма через SMTP: {str(error)}"
    elif isinstance(error, ValueError):
        return f"Неверное значение: {str(error)}"
    elif isinstance(error, KeyError):
        return f"Ключ не найден: {str(error)}"
    return "Неизвестная ошибка при отправке письма"


class EmailSender:
    def __init__(self, emails, mailing_type, release_type,
                 server_version=None, ipad_version=None, android_version=None, language='ru'):
        self.server_version = server_version
        self.emails = emails if isinstance(emails, list) else [emails]
        self.mailing_type = mailing_type
        self.release_type = release_type
        self.ipad_version = ipad_version or ''
        self.android_version = android_version or ''
        self.language = language
        self.logger = logger
        self.error_logger = logger
        self.msg = MIMEMultipart()
        self.env = Environment(loader=FileSystemLoader(
            os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML')
        ))
        self.config = self._load_config()

    @log_errors()
    def _load_config(self):
        """Load JSON configuration used by the mailing helpers.

        In the open-source version the configuration file is optional. When it
        is missing we return an empty dictionary so that the sender can be
        configured programmatically."""
        settings_data = get_integration_settings()
        if settings_data:
            return settings_data
        config_path = get_config_path()
        if not os.path.exists(config_path):
            return {}
        with open(config_path, 'r', encoding='utf-8-sig') as json_file:
            return json.load(json_file)

    def _structure_updates_3x(self, updates):
        structured_updates = []
        current_module = {"title": None, "updates": []}
        module_count = 1

        for update in updates:
            if 'BoardMaps Core:' in update:
                if current_module["updates"]:
                    structured_updates.append(current_module)
                current_module = {"title": f"{module_count}. BoardMaps Core:", "updates": []}
                module_count += 1
            elif 'Модуль' in update:
                if current_module["updates"]:
                    structured_updates.append(current_module)
                current_module = {"title": f"{module_count}. {update.split(':')[0]}:", "updates": []}
                module_count += 1
            else:
                current_module["updates"].append(update)

        if current_module["updates"]:
            structured_updates.append(current_module)

        if len(structured_updates) == 1:
            updates_only = structured_updates[0]["updates"]
            structured_updates[0]["title"] = structured_updates[0]["title"].replace("1. ", "")
            if len(updates_only) == 1:
                return [{"title": structured_updates[0]["title"], "updates": updates_only[0]}]
        return structured_updates

    def _get_template_name(self):
        lang = f'_{self.language}'
        r, m = self.release_type, self.mailing_type

        templates = {
            ('standard_mailing', 'release2x'): f'index_2x{lang}.html',
            ('standard_mailing', 'release3x'): f'index_3x{lang}.html',
            ('hotfix', 'release2x'): f'index_2x_hotfix_server{lang}.html',
            ('hotfix', 'release3x'): f'index_3x_hotfix_server{lang}.html',
            ('hotfix', 'releaseAndroid2x'): f'index_2x_hotfix_android{lang}.html',
            ('hotfix', 'releaseAndroid3x'): f'index_3x_hotfix_android{lang}.html',
            ('hotfix', 'releaseiPad2x'): f'index_2x_hotfix_ipad{lang}.html',
            ('hotfix', 'releaseiPad3x'): f'index_3x_hotfix_ipad{lang}.html',
            ('hotfix', 'releaseModule'): f'index_module_hotfix{lang}.html',
            ('hotfix', 'releaseIntegration'): f'index_integration_hotfix{lang}.html',
        }

        template = templates.get((m, r))
        if not template:
            raise FileNotFoundError(f"Шаблон не найден для release_type={r}, mailing_type={m}, language={self.language}")
        return template

    def _prepare_context(self):
        context = {
            'number_version': self.server_version,
            'server_updates': None,
            'ipad_updates': None,
            'android_updates': None
        }
        lang_key = {'ru': 'Русский', 'en': 'Английский'}.get(self.language, 'Русский')

        try:
            if self.mailing_type == 'standard_mailing':
                server_notes = get_server_release_notes(self.server_version, lang_key)
                # log_updates(self.logger, "Обновления сервера", server_notes, lang_key)

                if self.release_type == 'release3x':
                    structured = self._structure_updates_3x(server_notes)
                    context['server_updates'] = (
                        structured[0]['updates'] if len(structured) == 1 and isinstance(structured[0]['updates'], str)
                        else structured
                    )
                else:
                    context['server_updates'] = server_notes[0] if len(server_notes) == 1 else server_notes

                if self.ipad_version:
                    ipad_notes = get_ipad_release_notes(self.ipad_version, lang_key)
                    # log_updates(self.logger, "Обновления iPad", ipad_notes, lang_key)
                    context['ipad_updates'] = ipad_notes[0] if len(ipad_notes) == 1 else ipad_notes

                if self.android_version:
                    android_notes = get_android_release_notes(self.android_version, lang_key)
                    # log_updates(self.logger, "Обновления Android", android_notes, lang_key)
                    context['android_updates'] = android_notes[0] if len(android_notes) == 1 else android_notes

            elif self.mailing_type == 'hotfix':
                if self.release_type in ['release2x', 'release3x']:
                    server_notes = get_server_release_notes(self.server_version, lang_key)
                    # log_updates(self.logger, "Обновления сервера", server_notes, lang_key)
                    if self.release_type == 'release3x':
                        structured = self._structure_updates_3x(server_notes)
                        context['server_updates'] = (
                            structured[0]['updates'] if len(structured) == 1 and isinstance(structured[0]['updates'], str)
                            else structured
                        )
                    else:
                        context['server_updates'] = server_notes[0] if len(server_notes) == 1 else server_notes

                if self.release_type in ['releaseAndroid2x', 'releaseAndroid3x'] and self.android_version:
                    android_notes = get_android_release_notes(self.android_version, lang_key)
                    # log_updates(self.logger, "Обновления Android", android_notes, lang_key)
                    context['android_updates'] = android_notes[0] if len(android_notes) == 1 else android_notes

                if self.release_type in ['releaseiPad2x', 'releaseiPad3x'] and self.ipad_version:
                    ipad_notes = get_ipad_release_notes(self.ipad_version, lang_key)
                    # log_updates(self.logger, "Обновления iPad", ipad_notes, lang_key)
                    context['ipad_updates'] = ipad_notes[0] if len(ipad_notes) == 1 else ipad_notes
        except Exception as e:
            self.error_logger.error(f"Ошибка подготовки контекста: {e}")
            raise

        return context

    def _render_html(self, template_name, context):
        template = self.env.get_template(template_name)
        html = template.render(context)
        return embed_hidden_logo(html, self.language)

    def _get_subject(self):
        version = self.server_version or self.android_version or self.ipad_version
        if not version:
            raise ValueError("Ни одна версия не указана для темы письма.")
        return {
            'ru': f'Обновление BoardMaps {version}',
            'en': f'BoardMaps Update {version}'
        }.get(self.language, f'Обновление BoardMaps {version}')

    def _attach_html(self, html):
        self.msg.attach(MIMEText(html, 'html'))

    @retry(stop_max_attempt_number=5, wait_fixed=10000)
    @log_errors(extra_info=send_email_extra_info)
    def send_email(self):
        mail_settings = self.config['MAIL_SETTINGS']
        self.msg['From'] = mail_settings['FROM']
        self.msg['To'] = ", ".join(self.emails)
        self.msg['Subject'] = Header(self._get_subject(), 'utf-8')
        self.msg['Message-ID'] = make_msgid()

        # Перед отправкой подготовим всё
        update_documentation(self.language, self.release_type, self.server_version,
                             self.ipad_version, self.android_version, self.config)
        template = self._get_template_name()
        context = self._prepare_context()
        html = self._render_html(template, context)

        # Вставки
        self._attach_html(html)
        attach_images(self.msg, self.logger)
        attach_files(self.msg, self.language, self.logger)

        with SMTP(mail_settings['SMTP'], 587) as server:
            server.starttls()
            server.login(mail_settings['USER'], mail_settings['PASSWORD'])
            server.send_message(self.msg)
            self.logger.info(f"Письмо отправлено: {self.emails}")
            return True

    def build_message_for_client(self, client_id, emails):
        """Формирует письмо для конкретного клиента."""
        from apps.clients.models import Client

        client = Client.objects.get(pk=client_id)
        self.msg = MIMEMultipart()
        self.emails = emails if isinstance(emails, list) else [emails]
        self.language = client.language.code if client.language else 'ru'

        mail_settings = self.config['MAIL_SETTINGS_SUPPORT']
        self.msg['From'] = mail_settings['FROM']
        self.msg['To'] = ", ".join(self.emails)
        self.msg['Subject'] = Header(self._get_subject(), 'utf-8')
        self.msg['Message-ID'] = make_msgid()

        update_documentation(self.language, self.release_type, self.server_version,
                             self.ipad_version, self.android_version, self.config)
        template = self._get_template_name()
        context = self._prepare_context()
        html = self._render_html(template, context)
        self._attach_html(html)
        attach_images(self.msg, self.logger)
        attach_files(self.msg, self.language, self.logger)
        return self.msg
