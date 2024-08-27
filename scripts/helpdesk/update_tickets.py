import requests
import json
import os
import time
from main.models import ReportTicket, SLAPolicy
from scripts.helpdesk.response_time import SLACalculator
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from dotenv import load_dotenv
import logging
import traceback
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


class TicketUpdater:
    """
    Класс для обновления заявок в системе службы поддержки.

    Отвечает за автоматическое обновление информации по заявкам, получение данных о статусах,
    приоритетах и пользователях через API, а также сохранение обновленных данных заявок в базу данных.

    Attributes:
        session (requests.Session): Сессия для выполнения запросов к API.
        api_url (str): URL API для запросов.
        api_auth_user (str): Имя пользователя для аутентификации в API.
        api_auth_pass (str): Пароль для аутентификации в API.
        status_dict (dict): Словарь статусов заявок.
        priority_dict (dict): Словарь приоритетов заявок.
        type_dict (dict): Словарь типов заявок.
    """
    def __init__(self):
        """
        Инициализирует класс, загружая переменные окружения и настраивая сессию для запросов к API.
        """
        self.load_env()
        self.session = requests.Session()
        self.session.auth = (self.api_auth_user, self.api_auth_pass)
        self.session.headers.update({'Content-Type': 'application/json'})
        self.status_dict = self.fetch_statuses()
        self.priority_dict = self.fetch_priorities()
        self.type_dict = self.fetch_types()

    def load_env(self):
        """
        Загружает настройки из переменных окружения.
        """
        self.api_url = os.getenv('API_URL_TICKETS')
        self.api_auth_user = os.getenv('API_AUTH_USER')
        self.api_auth_pass = os.getenv('API_AUTH_PASS')

    def fetch_statuses(self):
        """
        Загружает и возвращает словарь статусов из API.

        Returns:
            dict: Словарь, где ключи - это ID статусов, а значения - их названия на русском.
        """
        status_url = f'{self.api_url}/statuses'
        try:
            response = self.session.get(status_url)
            response.raise_for_status()
            statuses = response.json()
            if 'data' not in statuses:
                logging.error('Ответ API не содержит ожидаемого ключа "data".')
                return {}
            return {status['id']: status['name']['ru'] for status in statuses['data']}
        except requests.HTTPError as http_err:
            logging.error(f'HTTP ошибка при запросе статусов: {http_err}')
            return {}
        except KeyError as key_err:
            logging.error(f'Ошибка ключа при обработке данных статусов: {key_err}')
            return {}
        except json.JSONDecodeError as json_err:
            logging.error(f'Ошибка декодирования JSON при запросе статусов: {json_err}')
            return {}
        except Exception as exc:
            logging.error(f'Неожиданная ошибка при запросе статусов: {exc}')
            return {}

    def fetch_priorities(self):
        """
        Загружает и возвращает словарь приоритетов из API.

        Returns:
            dict: Словарь, где ключи - это ID приоритетов, а значения - их названия на русском.
        """
        priority_url = f'{self.api_url}/priorities'
        try:
            response = self.session.get(priority_url)
            response.raise_for_status()
            priorities = response.json()
            if 'data' not in priorities:
                logging.error('Ответ API не содержит ожидаемого ключа "data".')
                return {}
            return {str(priority['id']): priority['name']['ru'] for priority in priorities['data']}
        except requests.HTTPError as http_err:
            logging.error(f'HTTP ошибка при запросе приоритетов: {http_err}')
            return {}
        except KeyError as key_err:
            logging.error(f'Ошибка ключа при обработке данных приоритетов: {key_err}')
            return {}
        except json.JSONDecodeError as json_err:
            logging.error(f'Ошибка декодирования JSON при запросе приоритетов: {json_err}')
            return {}
        except Exception as exc:
            logging.error(f'Неожиданная ошибка при запросе приоритетов: {exc}')
            return {}
    
    def fetch_types(self):
        """
        Загружает словарь типов заявок из API.

        Возвращает:
            dict: Словарь типов, где ключ - это идентификатор типа, а значение - его имя на русском языке.
        """
        type_url = f'{self.api_url}/types'
        try:
            response = self.session.get(type_url)
            response.raise_for_status()
            types = response.json().get('data', [])
            if not types:
                logging.error('API вернуло пустой список типов')
                return {}
            return {type_entry['id']: type_entry['name']['ru'] for type_entry in types if 'id' in type_entry and 'name' in type_entry}
        except requests.HTTPError as http_err:
            logging.error(f'HTTP ошибка при запросе к API типов: {http_err}')
        except requests.RequestException as req_err:
            logging.error(f'Ошибка связи при запросе к API типов: {req_err}')
        except ValueError as json_err:
            logging.error(f'Ошибка декодирования JSON: {json_err}')
        return {}
    
    def fetch_user_organization_name(self, user_id):
        """
        Получает название организации пользователя по его ID.

        Args:
            user_id (str): ID пользователя в системе.

        Returns:
            str: Название организации или 'Неизвестная компания' при отсутствии данных.
        """
        user_url = f'{self.api_url}/users/{user_id}'
        try:
            response = self.session.get(user_url)
            response.raise_for_status()
            user_data = response.json().get('data')
            if not user_data:
                logging.error("Ответ API не содержит данных пользователя.")
                return 'Неизвестная компания'
            organization_info = user_data.get('organization')
            if organization_info and isinstance(organization_info, dict) and 'name' in organization_info:
                return organization_info['name']
            return 'Клиент без компании'
        except requests.HTTPError as http_err:
            logging.error(f'HTTP ошибка при запросе к API пользователя: {http_err}')
        except requests.RequestException as req_err:
            logging.error(f'Ошибка при выполнении запроса пользователя: {req_err}')
        except ValueError as json_err:
            logging.error(f'Ошибка декодирования JSON: {json_err}')
        return 'Неизвестная компания'
    
    def parse_timedelta(self, time_str):
        """
        Преобразует строку времени в объект timedelta.

        Args:
            time_str (str): Строка времени в формате 'ЧЧ:ММ:СС'.

        Returns:
            timedelta: Объект timedelta, представляющий разницу времени.
        """
        try:
            hours, minutes, seconds = map(int, time_str.split(':'))
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except ValueError:
            logging.error(f"Ошибка преобразования времени из строки: {time_str}")
            return timedelta()

    def handle_custom_fields(self, custom_fields):
        """
        Обрабатывает пользовательские поля заявок.

        Args:
            custom_fields (list): Список пользовательских полей заявки.

        Returns:
            tuple: Возвращает кортеж с данными о причине, модуле, значении CI и плане.
        """
        cause = "Не указано"
        module_boardmaps = "Не указано"
        ci_value = ""
        plan = "Не указан"

        for field in custom_fields:
            field_id = field.get('id')
            field_value = field.get('field_value', {})

            if field_id == 2:  # Причины возникновения
                # Получаем только второй уровень из иерархии
                level_info = field_value.get('2', {})
                if level_info and 'name' in level_info and level_info['name']:
                    cause = level_info['name']['ru']

            elif field_id == 3:  # Модуль BoardMaps
                if field_value and 'name' in field_value and field_value['name']:
                    module_boardmaps = field_value['name']['ru']

            elif field_id == 8:  # CI Value
                ci_value = field_value

            elif field_id == 5:  # План
                plan = field_value

        return cause, module_boardmaps, ci_value, plan


    def check_sla_violation(self, sla_policy, sla_working_time, response_time):
        """
        Проверяет просроченность SLA на основе политики SLA.

        Args:
            sla_policy (SLAPolicy): Политика SLA для заявки.
            sla_working_time (timedelta): Время работы по заявке.
            response_time (timedelta): Время первого ответа по заявке.

        Returns:
            tuple: Кортеж (sla_violated, response_violated, sla_overdue_time, response_overdue_time)
        """
        sla_violated = sla_working_time > sla_policy.max_resolution_time
        response_violated = response_time > sla_policy.reaction_time

        sla_overdue_time = sla_working_time - sla_policy.max_resolution_time if sla_violated else None
        response_overdue_time = response_time - sla_policy.reaction_time if response_violated else None

        return sla_violated, response_violated, sla_overdue_time, response_overdue_time


    def update_tickets(self, start_date, end_date):
        """
        Обновляет заявки за указанный период времени.

        Args:
            start_date (str): Начальная дата обновления.
            end_date (str): Конечная дата обновления.

        Returns:
            list: Список всех обработанных заявок.
        """
        all_tickets = []
        params = {
            'department_list': 1,
            'from_date_updated': start_date,
            'to_date_updated': end_date,
            'page': 1
        }
        request = self.session.get(f'{self.api_url}/tickets', params=params)
        request_json = request.json()
        # Определяем общее количество страниц
        total_pages = request_json['pagination']['total_pages']

        # Обрабатываем и добавляем заявки первой страницы в общий список
        all_tickets.extend(self.process_tickets(request_json.get('data', {})))

        # Перебор и обработка заявок для оставшихся страниц
        for page in range(2, total_pages + 1):
            params['page'] = page
            request = self.session.get(f'{self.api_url}/tickets', params=params)
            request_json = request.json()
            all_tickets.extend(self.process_tickets(request_json.get('data', {})))

        return all_tickets

    def process_tickets(self, ticket_data_list):
        """
        Обрабатывает список данных заявок.

        Args:
            ticket_data_list (list): Список данных заявок.

        Returns:
            list: Список обработанных заявок.
        """
        processed_tickets = []
        
        # Проверка на пустой список
        if not ticket_data_list:
            logging.info("Список данных заявок пуст, обработка пропущена.")
            return processed_tickets
        
        for ticket_key, ticket_data in ticket_data_list.items():
            if ticket_data is None:
                logging.error(f"Данные заявки {ticket_key} отсутствуют.")
                continue
            try:
                # Игнорируем заявки с type_id равным 9
                if ticket_data.get('type_id') == 9:
                    logging.info(f"Заявка {ticket_data['id']} с типом 'Обновление' (type_id=9) исключена из обработки.")
                    continue
                processed_tickets.append(self.update_single_ticket(ticket_data))
            except Exception as error:
                logging.error(f'Ошибка при обработке заявки {ticket_key}: {error}\n{traceback.format_exc()}')
        
        return processed_tickets

    def update_single_ticket(self, ticket_data):
        """
        Собирает информацию об одной заявке на основе предоставленных данных.

        Args:
            ticket_data (dict): Данные одной заявки.

        Raises:
            ValueError: Если данные заявки отсутствуют.

        Returns:
            dict: Результат обновления заявки.
        """
        if ticket_data is None:
            raise ValueError("Данные заявки не предоставлены")

        if ticket_data.get('type_id') == 9:
            logging.info(f"Обновление заявки {ticket_data['id']} пропущено, так как тип 'Обновление' (type_id=9).")
            return None  # Пропускаем обновление заявки

        closed_date = None
        ci_value = None
        plan = "Не указан"
        try:
            ticket_id = ticket_data['id']
            unique_id = ticket_data.get('unique_id')
            status = self.status_dict.get(ticket_data['status_id'], "Неизвестный статус")
            subject = ticket_data.get('title', '')
            type_name = self.type_dict.get(ticket_data['type_id'], "Неизвестный тип")
            creation_date = make_aware(datetime.strptime(ticket_data['date_created'], '%Y-%m-%d %H:%M:%S'))
            updated_date = make_aware(datetime.strptime(ticket_data['date_updated'], '%Y-%m-%d %H:%M:%S'))
            if ticket_data['status_id'] == "closed":
                closed_date = updated_date

            # Получение имени компании пользователя
            client_name = self.fetch_user_organization_name(ticket_data['user_id'])

            # Проверка и формирование имени исполнителя
            if ticket_data['owner_name'] and ticket_data['owner_lastname']:
                assignee_name = f"{ticket_data['owner_name']} {ticket_data['owner_lastname']}"
            else:
                assignee_name = "Нет исполнителя"

            initiator = f"{ticket_data['user_name']} {ticket_data['user_lastname']}"

            priority = self.priority_dict.get(str(ticket_data['priority_id']), "Неизвестный приоритет")

            rus_priority = priority

            sla = ticket_data['sla_flag']

            sla_calculator = SLACalculator(self.api_url, self.api_auth_user, self.api_auth_pass)
            # Получаем все события аудита для этой заявки
            events = sla_calculator.fetch_all_events(ticket_id)
            # Рассчитываем время SLA и время первого ответа
            sla_working_time_str, response_time_str = sla_calculator.calculate_sla_time(events)

            sla_working_time = self.parse_timedelta(sla_working_time_str)
            response_time = self.parse_timedelta(response_time_str)

            cause, module_boardmaps, ci_value, plan = self.handle_custom_fields(ticket_data.get('custom_fields', []))

            # Преобразование значений plan и priority
            plan_mapping = {
                'Platinum': 'platinum',
                'Gold': 'gold',
                'Silver': 'silver',
                'Bronze': 'bronze'
            }

            priority_mapping = {
                'Критический': 'critical',
                'Высокий': 'high',
                'Средний': 'medium',
                'Низкий': 'low'
            }

            plan = plan_mapping.get(plan, plan)
            priority = priority_mapping.get(priority, priority)

            # Получаем SLA план для проверки
            try:
                sla_policy = SLAPolicy.objects.get(priority=priority, plan=plan)
                sla_violated, response_violated, sla_overdue_time, response_overdue_time = self.check_sla_violation(
                    sla_policy, sla_working_time, response_time
                )
            except SLAPolicy.DoesNotExist as error:
                scripts_error_logger.error(f"Ошибка получения SLA плана заявки {ticket_id}, для приоритета '{priority}' и плана '{plan}': {error}")
                scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
                sla_violated = False
                response_violated = False
                sla_overdue_time = None
                response_overdue_time = None

            # Получение текущей даты
            today = datetime.now().date()

            # Отправляем данные в таблицу для сохранения изменений о заявке
            ticket, created = ReportTicket.objects.update_or_create(
                ticket_id=ticket_id,
                defaults={
                    'report_date': today,
                    'unique_id': unique_id,
                    'status': status,
                    'subject': subject,
                    'type_name': type_name,
                    'creation_date': creation_date,
                    'closed_date': closed_date,
                    'client_name': client_name,
                    'initiator': initiator,
                    'priority': rus_priority,
                    'assignee_name': assignee_name,
                    'updated_at': updated_date,
                    'last_reply_at': updated_date,
                    'sla': sla,
                    'sla_time': sla_working_time,
                    'first_response_time': response_time,
                    'sla_violated': sla_violated,
                    'response_violated': response_violated,
                    'sla_overdue_time': sla_overdue_time,
                    'response_overdue_time': response_overdue_time,
                    'cause': cause,
                    'module_boardmaps': module_boardmaps,
                    'ci': ci_value,
                    'staff_message': "0",
                }
            )

            if created:
                scripts_info_logger.info(f'Новая заявка {ticket_id} создана')
            else:
                scripts_info_logger.info(f'Заявка {ticket_id} обновлена')

            ### Выполняем паузу после сохранения данных, так как можно делать только 300 запросов в минуту
            time.sleep(5)
        except KeyError as key_error:
            scripts_error_logger.error(f'Ошибка обработки ключа: {key_error}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except ValueError as value_error:
            scripts_error_logger.error(f'Ошибка преобразования значения: {value_error}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except Exception as error_message:
            scripts_error_logger.error(f'Произошла ошибка при обновлении заявки {ticket_id}. Ошибка: {error_message}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

    def clean_up_tickets(self):
        """
        Проверяет все открытые заявки на предмет изменения департамента или пометки как удаленные.
        Удаляет заявки из базы данных, если они были перенесены из департамента '1' или помечены как удаленные.
        """
        open_tickets = ReportTicket.objects.exclude(status__in=["Closed", "Выполнено"])
        for ticket in open_tickets:
            ticket_url = f'{self.api_url}/tickets/{ticket.ticket_id}'
            try:
                response = self.session.get(ticket_url)
                response.raise_for_status()
                ticket_data = response.json().get('data')

                if ticket_data is None:
                    scripts_error_logger.error(f"Не удалось получить данные для заявки {ticket.ticket_id}")
                    continue

                ticket_department = ticket_data.get('department_id')
                ticket_deleted = ticket_data.get('deleted')
                ticket_locked = ticket_data.get('ticket_lock')
                ticket_type_id = ticket_data.get('type_id')

                if ticket_locked == 1 and ticket_deleted == 1:
                    # Обновляем статус и дату закрытия заявки в базе данных
                    today_date = datetime.now().date()
                    ticket.status = "Выполнено"
                    ticket.closed_date = today_date
                    ticket.save()
                    # Отправляем запрос на обновление статуса заявки в HDE
                    self.update_ticket_status(ticket.ticket_id, "closed")
                    scripts_info_logger.info(f'Статус заявки {ticket.ticket_id} обновлён на "Выполнено" из-за объединения.')
                    continue

                # Проверка условий для удаления заявки из базы данных
                if ticket_department != 1 or ticket_deleted == 1 or ticket_type_id == 9:
                    reason_parts = []
                    if ticket_deleted == 1:
                        reason_parts.append("удалена")
                    if ticket_department != 1:
                        reason_parts.append("переведена из ТП")
                    if ticket_type_id == 9:
                        reason_parts.append("тип заявки 'Обновление'")
                    
                    reason_message = ', '.join(reason_parts)  # Соединяем части сообщения через запятую
                    scripts_info_logger.info(f'Удаление заявки {ticket.ticket_id} из базы данных. Причина: {reason_message}')
                    ticket.delete()  # Удаление заявки из базы данных

            except requests.HTTPError as http_err:
                scripts_error_logger.error(f'HTTP ошибка при запросе заявки {ticket.ticket_id}: {http_err}')
                scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
            except requests.RequestException as req_err:
                scripts_error_logger.error(f'Ошибка связи при запросе заявки {ticket.ticket_id}: {req_err}')
                scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
            except ValueError as json_err:
                scripts_error_logger.error(f'Ошибка декодирования JSON для заявки {ticket.ticket_id}: {json_err}')
                scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
            except Exception as exc:
                scripts_error_logger.error(f'Неожиданная ошибка при обработке заявки {ticket.ticket_id}: {exc}')
                scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
    
    def update_ticket_status(self, ticket_id, status_id):
        """
        Обновляет статус заявки в HelpDeskEddy.

        Args:
            ticket_id (int): ID заявки.
            status_id (str): Новый статус заявки.
        """
        update_url = f'{self.api_url}/tickets/{ticket_id}'
        data = {'status_id': status_id}
        try:
            response = self.session.put(update_url, json=data)
            response.raise_for_status()
            scripts_info_logger.info(f'Статус заявки {ticket_id} успешно обновлен в HDE.')
        except requests.HTTPError as http_err:
            scripts_error_logger.error(f'HTTP ошибка при запросе заявки {ticket_id}: {http_err}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except requests.RequestException as req_err:
            scripts_error_logger.error(f'Ошибка связи при запросе заявки {ticket_id}: {req_err}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except ValueError as json_err:
            scripts_error_logger.error(f'Ошибка декодирования JSON для заявки {ticket_id}: {json_err}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except Exception as exc:
            scripts_error_logger.error(f'Неожиданная ошибка при обработке заявки {ticket_id}: {exc}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")

    def fetch_tickets(self, client_name, start_date, end_date):
        """
        Запрашивает данные о заявках из тикет-системы для заданного клиента и периода времени.

        Args:
            client_name (str): Имя клиента.
            start_date (date): Начальная дата.
            end_date (date): Конечная дата.

        Returns:
            list: Список заявок.
        """
        params = {
            'client_name': client_name,
            'from_date_updated': start_date.strftime('%Y-%m-%d'),
            'to_date_updated': end_date.strftime('%Y-%m-%d')
        }
        try:
            response = self.session.get(f'{self.api_url}/tickets', params=params)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.HTTPError as http_err:
            scripts_error_logger.error(f'HTTP ошибка при запросе данных о заявках для клиента {client_name}: {http_err}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except requests.RequestException as req_err:
            scripts_error_logger.error(f'Ошибка связи при запросе данных о заявках для клиента {client_name}: {req_err}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except ValueError as json_err:
            scripts_error_logger.error(f'Ошибка декодирования JSON для данных о заявках для клиента {client_name}: {json_err}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        except Exception as exc:
            scripts_error_logger.error(f'Неожиданная ошибка при запросе данных о заявках для клиента {client_name}: {exc}')
            scripts_error_logger.error(f"Трассировки стека: {traceback.format_exc()}")
        return []
