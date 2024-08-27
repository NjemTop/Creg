import requests
from datetime import datetime, timedelta, date
import os
import re
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SLACalculator:
    def __init__(self, api_url, auth_user, auth_pass):
        """
        Инициализирует калькулятор SLA с указанными параметрами API.

        Args:
            api_url (str): URL API для запроса данных аудита.
            auth_user (str): Имя пользователя для аутентификации API.
            auth_pass (str): Пароль пользователя для аутентификации API.
        """
        self.api_url = api_url
        self.auth = (auth_user, auth_pass)
        self.holidays_cache = {}  # Словарь для кэширования данных о праздниках по годам
    
    def load_holidays(self, year):
        """
        Загружает и кэширует данные о праздничных и сокращенных рабочих днях для указанного года.
        
        Args:
            year (int): Год, для которого необходимо загрузить данные о праздниках.
        
        Returns:
            tuple: Кортеж, содержащий два множества: множество праздничных дней и множество сокращенных рабочих дней.
        
        Кэширует данные о праздниках для уменьшения количества запросов к API в случае повторных вызовов.
        В случае ошибки при запросе к API возвращает пустые множества.
        """
        if year in self.holidays_cache:
            return self.holidays_cache[year]  # Возврат данных из кэша, если они уже загружены

        url = f"https://xmlcalendar.ru/data/ru/{year}/calendar.json"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Проверка успешности HTTP-запроса
            holidays_data = response.json()
            holidays_set = set()
            shortened_days_set = set()  # Множество для сокращенных рабочих дней

            # Перебор данных о каждом месяце
            for month_data in holidays_data['months']:
                month = month_data['month']
                days = month_data['days'].split(',')
                for day in days:
                    day_info = day.split('*')[0].split('+')[0]  # Удаление специальных символов
                    day_number = int(day_info)
                    holiday_date = date(year, month, day_number)
                    holidays_set.add(holiday_date)
                    if '*' in day:  # Проверка на сокращенный день
                        shortened_days_set.add(holiday_date)

            # Кэширование загруженных данных
            self.holidays_cache[year] = (holidays_set, shortened_days_set)
            return holidays_set, shortened_days_set  # Возврат загруженных данных
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка загрузки данных о праздниках: {e}")
            return set(), set()  # Возврат пустых множеств в случае ошибки

    def get_audit_data(self, ticket_id, page=1):
        """
        Получает данные аудита для указанного тикета и страницы.

        Args:
            ticket_id (int): ID тикета для запроса данных аудита.
            page (int, optional): Номер страницы данных аудита. По умолчанию 1.

        Returns:
            tuple: Кортеж, содержащий список событий и данные пагинации.
        """
        url = f"{self.api_url}/tickets/{ticket_id}/audit?page={page}"
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()  # Проверяем на наличие ошибок HTTP
            response_json = response.json()
            ### Проверяем наличие необходимых данных в ответе
            if 'data' in response_json and 'pagination' in response_json:
                ### Получаем события и данные пагинации
                data = response_json.get('data', {})
                pagination = response_json.get('pagination', {})
                ### Сортируем и возвращаем события
                events = [data[key] for key in sorted(data.keys(), key=int) if data[key].get('date_created')]
                return events, pagination
            else:
                logging.warning('Ответ API не содержит ожидаемых ключей "data" или "pagination".')
                return [], None
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка запроса: {e}")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Произошла HTTP-ошибка: {http_err}")
        except Exception as err:
            logging.error(f"Произошла ошибка: {err}")
        return [], None

    def add_working_time(self, start, end):
        """
        Рассчитывает рабочее время между двумя моментами времени, учитывая только рабочие часы и дни.

        Args:
            start (datetime): Начальное время для расчета.
            end (datetime): Конечное время для расчета.

        Returns:
            timedelta: Время, проведенное в рабочие часы между начальным и конечным временем.
        """
        if start is None or end is None:
            logging.warning("Одно из значений времени None: start={start}, end={end}")
            return timedelta()
        ### Проверяем корректность диапазона времени
        if start >= end:
            logging.warning('Начальное время больше или равно конечному.')
            return timedelta()

        sla_time = timedelta()
        current = start

        while current < end:
            year = current.year
            if year not in self.holidays_cache:
                self.load_holidays(year)
            holidays, shortened_days = self.holidays_cache[year]

            ### Проверяем, является ли текущий день рабочим по календарю
            if current.date() not in holidays:
                start_of_day = current.replace(hour=9, minute=0, second=0, microsecond=0)
                # Проверяем, является ли день сокращенным
                if current.date() in shortened_days:
                    end_of_day = current.replace(hour=18, minute=0, second=0, microsecond=0)  # Сокращенный рабочий день
                else:
                    end_of_day = current.replace(hour=19, minute=0, second=0, microsecond=0)  # Обычный рабочий день
                
                ### Переходим к началу рабочего дня, если текущее время раньше
                if current < start_of_day:
                    current = start_of_day
                
                ### Проверяем, не закончился ли уже рабочий день
                if current >= end_of_day:
                    current += timedelta(days=1)
                    current = current.replace(hour=0, minute=0, second=0, microsecond=0)
                    continue
                
                ### Рассчитываем время в рабочих часах
                if end < end_of_day:
                    sla_time += end - current
                    # logging.info(f"Adding time from {current} to {end}, итого: {end - current}")
                    break
                else:
                    sla_time += end_of_day - current
                    # logging.info(f"Adding time from {current} to {end_of_day}, итого {end_of_day - current}")
                    current = end_of_day + timedelta(days=1)
                    current = current.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                ### Если не рабочий день, переходим к следующему дню
                current += timedelta(days=1)
                current = current.replace(hour=0, minute=0, second=0, microsecond=0)

        # logging.info(f"Расчетное время SLA: {sla_time}")
        return sla_time

    def parse_status_change(self, status_text):
        """
        Анализирует текст изменения статуса и извлекает из него старый и новый статусы.

        Args:
            status_text (str): Текстовое описание изменения статуса.

        Returns:
            tuple: кортеж с двумя элементами (старый статус, новый статус) или (None, None), если сопоставление не удалось.
        """
        match = re.search(r'с <strong>"([^"]+)"</strong> на <strong>"([^"]+)"</strong>', status_text)
        if match:
            return match.groups()  # Возвращает кортеж (старый статус, новый статус)
        return None, None

    def handle_status_update(self, old_status, new_status, prev_time, event_time, sla_active):
        """
        Обрабатывает изменения статуса и определяет изменения в подсчёте SLA.

        Args:
            old_status (str): Старый статус заявки.
            new_status (str): Новый статус заявки.
            prev_time (datetime): Время последнего события.
            event_time (datetime): Время текущего события.
            sla_active (bool): Флаг активности SLA.

        Returns:
            tuple: (timedelta, bool), где timedelta - приращение времени SLA, bool - новое состояние активности SLA.
        """
        sla_time_increment = timedelta()
        ### Если статус переходит с "Открыто" на "В работе", игнорируем это как несущественное для SLA
        if old_status == "Открыто" and new_status == "В работе":
            return sla_time_increment, sla_active

        ### Остановка SLA при переходе в статус "Ожидание ответа от клиента"
        if new_status == "Ожидание ответа от клиента":
            if sla_active and prev_time:
                sla_time_increment = self.add_working_time(prev_time, event_time)
                return sla_time_increment, False
            return sla_time_increment, False

        ### Возобновление SLA при выходе из статуса "Ожидание ответа от клиента", если заявка не "Выполнена"
        if old_status == "Ожидание ответа от клиента" and new_status != "Выполнено":
            return sla_time_increment, True

        ### Остановка SLA при переходе в статус "Выполнено"
        if new_status == "Выполнено":
            if sla_active and prev_time:
                sla_time_increment = self.add_working_time(prev_time, event_time)
                return sla_time_increment, False
            return sla_time_increment, False

        ### Продолжение подсчёта SLA для других активных статусов
        if sla_active:
            return sla_time_increment, True

        return sla_time_increment, sla_active
    
    def format_duration(self, duration):
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"

    def calculate_sla_time(self, events):
        """
        Рассчитывает общее SLA время на основе событий аудита и время до первого ответа.

        Args:
            events (list): Список событий аудита для расчета.

        Returns:
            tuple: (timedelta, timedelta) - общее SLA время и время до первого ответа.
        """
        sla_time = timedelta()  # Инициализируем счетчик SLA времени
        prev_time = None  # Время последнего рассматриваемого события
        sla_active = True  # Проверка активного статуса подсчёта SLA
        first_response_time = None  # Время до первого ответа
        first_response_recorded = False  # Флаг, что первый ответ уже учтен
        ticket_creation_time = None  # Время создания заявки

        for event in events:
            try:
                ### Преобразуем строку времени события в объект datetime
                event_time = datetime.strptime(event["date_created"], "%H:%M:%S %d.%m.%Y")
            except ValueError as error:
                logging.error(f"Ошибка преобразования даты: {error}")
                continue

            event_type = event['event']

            if event_type == 'ticket_create':
                ### Записываем время создания тикета и начинаем отсчёт SLA
                ticket_creation_time = event_time
                prev_time = event_time
                # logging.info("Тикет создан: {}".format(prev_time))

            elif event_type == 'status_update':
                ### Получаем текст изменения статуса и обрабатываем его
                status_text = event["text"].get('ru', '')
                # logging.info("{} - Дата изменения: {}".format(status_text, event_time))
                old_status, new_status = self.parse_status_change(status_text)
                time_increment, update_sla_active = self.handle_status_update(
                    old_status, new_status, prev_time, event_time, sla_active)
                ### Добавляем время SLA, если оно было активно
                sla_time += time_increment
                if update_sla_active != sla_active:
                    ### Обновляем статус активности SLA
                    sla_active = update_sla_active
                    if sla_active:
                        ### Обновляем время последнего события для следующего подсчета времени SLA
                        prev_time = event_time

            elif event_type == 'ticket_answer' and not first_response_recorded and event['group_id'] != 1:
                ### Учитываем первый ответ, если это ответ поддержки (не клиента)
                if first_response_time is None:
                    first_response_time = self.add_working_time(ticket_creation_time, event_time)
                    first_response_recorded = True
                # logging.info(f"Первый ответ дан в {event_time}, время до первого ответа: {first_response_time}")

        ### Добавляем время до текущего момента, если SLA все еще активно и не было ответа
        if sla_active and prev_time:
            current_time = datetime.now()
            sla_time += self.add_working_time(prev_time, current_time)

        if not first_response_time and not first_response_recorded:
            # Если не было ответа и заявка закрыта, считаем время до закрытия
            first_response_time = sla_time if sla_time else timedelta(0)

        formatted_sla_time = self.format_duration(sla_time)
        formatted_first_response_time = self.format_duration(first_response_time)
        return formatted_sla_time, formatted_first_response_time

    def fetch_all_events(self, ticket_id):
        """
        Извлекает все события аудита для указанного тикета.

        Args:
            ticket_id (int): ID тикета для извлечения событий аудита.

        Returns:
            list: Список всех событий аудита, отсортированных по дате создания.
        """
        all_events = []
        page = 1
        while True:
            events, pagination = self.get_audit_data(ticket_id, page)
            if not events:  # Если возникла ошибка при получении данных
                break
            all_events.extend(events)
            if not pagination or page >= pagination.get("total_pages", 0):
                break
            page += 1
        ### Сортируем события по времени создания
        return sorted(all_events, key=lambda x: datetime.strptime(x["date_created"], "%H:%M:%S %d.%m.%Y"))

if __name__ == "__main__":
    load_dotenv()
    API_URL = os.environ.get('API_URL_TICKETS')
    API_AUTH_USER = os.environ.get('API_AUTH_USER')
    API_AUTH_PASS = os.environ.get('API_AUTH_PASS')

    sla_calculator = SLACalculator(API_URL, API_AUTH_USER, API_AUTH_PASS)
    all_events_sorted = sla_calculator.fetch_all_events(ticket_id=216)
    total_sla_time, first_response_time = sla_calculator.calculate_sla_time(all_events_sorted)
    logging.info('\x1b[6;36;43m' + f"Время первого ответа: {first_response_time}" + '\x1b[0m')
    logging.info('\x1b[6;30;42m' + f"Общее время SLA: {total_sla_time}" + '\x1b[0m')
    