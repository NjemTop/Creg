from django.core.mail import EmailMessage
from django.db.models.fields import Field
from main.models import (Integration, ContactsCard, ConnectInfoCard, 
                         BMServersCard, Integration, ModuleCard, 
                         TechAccountCard, ConnectionInfo, 
                         ServiseCard, TechInformationCard)
import json
import ast
from datetime import date
import logging


# Настройка логгера
logger = logging.getLogger(__name__)

def convert_date_objects(data):
    """
    Функция для конвертации объектов даты в строковый формат.
    """
    try:
        for key, value in data.items():
            if isinstance(value, date):
                # Преобразование объекта date в строку
                data[key] = str(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        # Рекурсивный вызов для вложенных словарей
                        convert_date_objects(item)
            elif isinstance(value, dict):
                # Рекурсивный вызов для словарей
                convert_date_objects(value)
        return data
    except Exception as e:
        logger.error("Ошибка при конвертации даты: %s", e)

# Получение русских названий из моделей
def get_verbose_fields(model):
    """
    Функция для извлечения имен полей и их человекочитаемых названий из моделей Django.
    """
    try:
        verbose_fields = {}
        for field in model._meta.fields:
            if isinstance(field, Field):
                # Сохранение читаемых названий полей
                verbose_fields[field.name] = field.verbose_name
        return verbose_fields
    except Exception as e:
        logger.error("Ошибка при получении verbose fields для модели %s: %s", model.__name__, e)
        raise

# Получение verbose fields для различных моделей
CONTACTS_CARD_VERBOSE_FIELDS = get_verbose_fields(ContactsCard)
INTEGRATION_VERBOSE_FIELDS = get_verbose_fields(Integration)
MODULE_VERBOSE_FIELDS = get_verbose_fields(ModuleCard)
CONNECT_INFO_CARD_VERBOSE_FIELDS = get_verbose_fields(ConnectInfoCard)
BM_SERVERS_CARD_VERBOSE_FIELDS = get_verbose_fields(BMServersCard)
TECH_ACCOUNT_CARD_VERBOSE_FIELDS = get_verbose_fields(TechAccountCard)
SERVISE_CARD_VERBOSE_FIELDS = get_verbose_fields(ServiseCard)
TECH_INFORMATION_VERBOSE_FIELDS = get_verbose_fields(TechInformationCard)

# Функция для форматирования данных в таблицу HTML
def format_as_html_table(data_dict, verbose_fields=None):
    """
    Функция для форматирования данных в виде HTML-таблицы.
    """
    try:
        html_str = '''
        <table style="width: 100%; border-collapse: collapse;">
        '''
        for key, value in data_dict.items():
            if verbose_fields:
                readable_key = verbose_fields.get(key, key)
            else:
                readable_key = key
            html_str += f'''
            <tr style="border: 1px solid black;">
                <td style="padding: 8px; border: 1px solid black;">{readable_key}</td>
                <td style="padding: 8px; border: 1px solid black;">{value}</td>
            </tr>
            '''
        html_str += "</table>"
        return html_str
    except Exception as e:
        logger.error("Ошибка при форматировании HTML таблицы: %s", e)
        raise

# Функция для отправки электронной почты
def send_email_alert_async(client_data, additional_data):
    """
    Функция для асинхронной отправки электронной почты с информацией о клиенте.
    """
    try:
        subject = f'Новый клиент создан в системе "Creg"'
        message = f"""
        <h1>Добрый день!</h1>
        <p>В системе "Creg" создан новый клиент.</p>
        {format_as_html_table(client_data)}
        """
        
        # Сопоставление полей с их verbose names для различных моделей
        verbose_fields_mapping = {
            'Контакты клиента': CONTACTS_CARD_VERBOSE_FIELDS,
            'Интеграции': INTEGRATION_VERBOSE_FIELDS,
            'Информация о подключениях к клиенту': CONNECT_INFO_CARD_VERBOSE_FIELDS,
            'Сервера BoardMaps': BM_SERVERS_CARD_VERBOSE_FIELDS,
            'Техническая учётная запись': TECH_ACCOUNT_CARD_VERBOSE_FIELDS,
            'Модули': MODULE_VERBOSE_FIELDS,
            'Обслуживание': SERVISE_CARD_VERBOSE_FIELDS,
            'Техническая информация': TECH_INFORMATION_VERBOSE_FIELDS,
        }
        
        # Обработка дополнительных данных о клиенте
        for key, value in additional_data.items():
            if key in verbose_fields_mapping:
                verbose_fields = verbose_fields_mapping[key]
                # Проверим, является ли значение строкой, которую можно преобразовать в список или словарь
                if isinstance(value, str) and (value.startswith('[') or value.startswith('{')) and (value.endswith(']') or value.endswith('}')):
                    try:
                        # Преобразование дат в строки, если строка может быть преобразована в словарь или список
                        if value.startswith('[') or value.startswith('{'):
                            try:
                                value_temp = json.loads(value)
                            except json.JSONDecodeError:
                                value_temp = None

                            if value_temp is not None:
                                value_temp = convert_date_objects(value_temp)
                                value = json.dumps(value_temp)

                        # Попытка преобразования строки в Python объект
                        value = ast.literal_eval(value)
                    except ValueError as e:
                        logging.error(f"Ошибка в ast.literal_eval(): {e}")

                if isinstance(value, list):
                    formatted_data_list = []
                    for sub_dict in value:
                        formatted_data = format_as_html_table(sub_dict, verbose_fields=verbose_fields)
                        formatted_data_list.append(formatted_data)
                    message += f"<h2>{key}</h2>{''.join(formatted_data_list)}"
                elif isinstance(value, dict):
                    formatted_data = format_as_html_table(value, verbose_fields=verbose_fields)
                    message += f"<h2>{key}</h2>{formatted_data}"
                else:
                    message += f"<p>{key}: {value}</p>"
            else:
                message += f"<p>{key}: {value}</p>"
        
        # Установка получателей письма и отправка
        recipient = ['oleg.eliseev@boardmaps.ru', 'denis.zhuravlev@boardmaps.ru', 'maxim.sorokin@boardmaps.ru']
        email = EmailMessage(subject, message, to=recipient)
        email.content_subtype = "html"
        email.send()
        logging.info("Письмо успешно отправлено на адреса: %s", ", ".join(recipient))

    except Exception as e:
        logging.error("Произошла ошибка при отправке письма: %s", e)
