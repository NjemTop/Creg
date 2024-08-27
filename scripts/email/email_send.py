import logging
import os
import smtplib
import traceback
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from dotenv import load_dotenv
from main.models import UsersBoardMaps, ContactsCard
from scripts.email.settings import set_email_config
from logger.log_config import setup_logger, get_abs_log_path


class EmailService:
    def __init__(self):
        load_dotenv()
        self.ticket_url = os.getenv('TICKET_URL', 'https://cs.boardmaps.ru/')
        self.nextcloud_url = os.getenv('NEXTCLOUD_URL', 'https://cloud.boardmaps.ru/')
        self.jfrog_url = os.getenv('JFROG_URL', 'https://dr.boardmaps.ru/')
        self.support_email = os.getenv('SUPPORT_EMAIL', 'support@boardmaps.ru')

        self.error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
        self.info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

    def send_client_creation_email(self, client_instance, tech_info, contact_data, module_data):
        """
        Отправляет уведомление о создании нового клиента на электронную почту.

        Args:
            client_instance (ClientsList): Экземпляр созданного клиента.
            tech_info (TechInformationCard): Техническая информация клиента.
            contacts (ContactFormSet): Набор форм контактов клиента.
            module_instance (ModuleCard): Информация о модулях клиента.

        Функция получает список пользователей, которым необходимо отправить уведомление,
        формирует контекст для шаблона письма, генерирует HTML и текстовое содержимое письма,
        и отправляет письмо каждому из указанных получателей.
        """
        try:
            # Устанавливаем конфигурацию для внутренней почты
            set_email_config('internal')

            # Получаем список пользователей для рассылки
            recipients = list(UsersBoardMaps.objects.filter(new_client=True).values_list('email', flat=True))

            # Проверяем, есть ли получатели для отправки уведомлений
            if not recipients:
                self.error_logger.error("Нет получателей для отправки уведомления о создании нового клиента.")
                return

            # Создаем контекст для шаблона письма
            context = {
                'client': client_instance,
                'contacts': contact_data,
                'modules': module_data,
                'tech_info': tech_info,
            }

            # Генерируем содержимое письма из шаблона
            html_content = render_to_string('emails/new_client_created.html', context)
            subject = f'Создан новый клиент "{client_instance.client_name}"'

            # Создаем и отправляем email
            email = EmailMultiAlternatives(subject, strip_tags(html_content), settings.DEFAULT_FROM_EMAIL, recipients)
            email.attach_alternative(html_content, "text/html")
            email.send()
            self.info_logger.info(f"Уведомление о создании нового клиента '{client_instance.client_name}' успешно отправлено.")
            return None  # Успех
        except smtplib.SMTPException as e:
            error_message = f"SMTP ошибка при отправке уведомления о создании нового клиента: {e}"
        except ImproperlyConfigured as e:
            error_message = f"Ошибка конфигурации при отправке уведомления о создании нового клиента: {e}"
        except Exception as e:
            error_message = f"Неизвестная ошибка при отправке уведомления о создании нового клиента: {e}"
        self.error_logger.error(error_message)
        self.error_logger.error(traceback.format_exc())
        return error_message  # Возвращаем описание ошибки


    def send_welcome_email(self, contact, password):
        """
        Отправляет приветственное письмо новому пользователю с данными для входа.

        Args:
            contact (dict): Словарь данных контакта, который содержит информацию о новом пользователе.
            password (str): Пароль, который был установлен для пользователя.
        """
        try:
            # Устанавливаем конфигурацию для продовской почты
            set_email_config('prod')

            # Используем данные из переданного словаря
            client_card = ContactsCard.objects.get(contact_email=contact['contact_email'])
            client = client_card.client_card.client_info

            client_login = client.short_name if client.short_name else "client_name"
            jfrog_password = client.password if client.password else "client_password"

            context = {
                'firstname': contact['firstname'],
                'ticket_url': self.ticket_url,
                'nextcloud_url': self.nextcloud_url,
                'jfrog_url': self.jfrog_url,
                'email': contact['contact_email'],
                'password': password,
                'nextcloud_login': client_login,
                'nextcloud_password': f"{client_login}321",
                'jfrog_login': client_login,
                'jrog_password': jfrog_password,
                'support_email': self.support_email,
            }
            html_content = render_to_string('emails/welcome_email.html', context)
            subject = 'Добро пожаловать на портал поддержки BoardMaps!'
            email = EmailMultiAlternatives(subject, strip_tags(html_content), settings.DEFAULT_FROM_EMAIL, [contact['contact_email']])
            email.attach_alternative(html_content, "text/html")
            email.send()

            self.info_logger.info(f"Приветственное письмо успешно отправлено на {contact['contact_email']}.")
        except ContactsCard.DoesNotExist:
            self.error_logger.error(f"Контакт с почтой {contact['contact_email']} не найден.")
        except Exception as e:
            self.error_logger.error(f"Ошибка при отправке приветственного письма: {str(e)}")
            self.error_logger.error(traceback.format_exc())

    def send_support_transition_email(self, client_instance, contacts_data):
        """
        Отправляет уведомление о переводе клиента на Техническую Поддержку (ТП).

        Args:
            client_instance (ClientsList): Экземпляр клиента, который был переведен на ТП.
            contacts_data (list): Список контактов клиента.
        """
        try:
            # Устанавливаем конфигурацию для внутренней почты
            set_email_config('internal')

            # Указываем получателей
            recipients = ['pmo@boardmaps.ru', 'account.management@boardmaps.ru', 'oleg.eliseev@boardmaps.ru']

            # Проверяем, есть ли получатели для отправки уведомлений
            if not recipients:
                self.error_logger.error("Нет получателей для отправки уведомления о переводе клиента на ТП.")
                return

            # Создаем контекст для шаблона письма
            context = {
                'client': client_instance,
                'contacts': contacts_data,
            }

            # Генерируем содержимое письма из шаблона
            html_content = render_to_string('emails/client_support_transition.html', context)
            subject = f'Клиент "{client_instance.client_name}" переведен на ТП'

            # Создаем и отправляем email
            email = EmailMultiAlternatives(subject, strip_tags(html_content), settings.DEFAULT_FROM_EMAIL, recipients)
            email.attach_alternative(html_content, "text/html")
            email.send()
            self.info_logger.info(f"Уведомление о переводе клиента '{client_instance.client_name}' на ТП успешно отправлено.")
            return None  # Успех
        except smtplib.SMTPException as e:
            error_message = f"SMTP ошибка при отправке уведомления о переводе клиента на ТП: {e}"
        except ImproperlyConfigured as e:
            error_message = f"Ошибка конфигурации при отправке уведомления о переводе клиента на ТП: {e}"
        except Exception as e:
            error_message = f"Неизвестная ошибка при отправке уведомления о переводе клиента на ТП: {e}"
        self.error_logger.error(error_message)
        self.error_logger.error(traceback.format_exc())
        return error_message  # Возвращаем описание ошибки
