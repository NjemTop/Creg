import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv
import time
import logging
from logger.log_config import setup_logger, get_abs_log_path


scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

load_dotenv()

class HelpDeskEddyClient:
    """
    Класс для взаимодействия с API HelpDeskEddy для создания заявок на сервисные запросы и уведомления SaaS.

    Атрибуты:
        retries (int): Количество попыток повторной отправки запроса в случае ошибки.
        timeout (int): Время ожидания ответа от сервера в секундах.
        api_url (str): URL API для создания заявок.
        session (requests.Session): Сессия для выполнения HTTP-запросов с поддержкой аутентификации.
    """

    def __init__(self, retries=3, timeout=5):
        """
        Инициализация класса HelpDeskEddyClient.

        Параметры:
            retries (int): Количество попыток повторной отправки запроса (по умолчанию 3).
            timeout (int): Время ожидания ответа от сервера в секундах (по умолчанию 5).
        """
        self.api_url = os.environ.get('API_URL_TICKETS')
        self.session = requests.Session()
        self.session.auth = (os.environ.get('API_AUTH_USER'), os.environ.get('API_AUTH_PASS'))
        self.retries = retries
        self.timeout = timeout

    def send_service_request(self, version, user_email, cc_emails=None):
        """
        Отправляет запрос на создание заявки для обновления версии сервера.

        Параметры:
            version (str): Версия обновления.
            user_email (str): Email основного получателя заявки ("Кому").
            cc_emails (list): Список email для копии ("Копия") (по умолчанию None).

        Возвращает:
            dict: JSON ответ от сервера с данными созданной заявки.
        """
        title = f"Обновление BoardMaps {version}"
        
        description_html = f"""
        <body style="margin: 0; padding: 0;">
            <font style="color: #2f2f2f; font-family: Arial, sans-serif; font-size: 14px; line-height: 16px;" align="justify">
                <table border="0" align="left" width="100%" height="auto" cellpadding="0" cellspacing ="0" background-size= "contain" background-repeat="no-repeat" background-position="left">
                <tr>
                <td>
                    <table style="border-collapse:collapse;" border="0" width="95%" cellpadding="0" cellspacing ="0" align="center">
                        <tr>
                            <td>
                                Добрый день!
                                <br><br>
                                <p>Сообщаем Вам о выходе новой версии серверной части приложения - <b>{version}</b>, в которую внесены функциональные улучшения.</p>
                                <br>
                                <p><ins>Просим согласовать сервисное окно, для установки обновления.</ins></p>
                                <br>
                                <p>Для скачивания документации, Вы можете воспользоваться ссылкой: <a href="https://cloud.boardmaps.ru" target="_blank" rel="noopener noreferrer">https://cloud.boardmaps.ru</a> </p>
                                <br>
                            </td>
                        </tr>
                    </td>
                </tr>
                </table>
            </font>
        </body>
        """
        
        return self._create_ticket(title, description_html, user_email, cc_emails)

    def send_saas_notification(self, version, user_email, date_time, cc_emails=None):
        """
        Отправляет уведомление SaaS-клиентам о запланированных работах по обновлению.

        Параметры:
            version (str): Версия обновления.
            user_email (str): Email основного получателя уведомления ("Кому").
            date_time (str): Дата и время запланированных работ.
            cc_emails (list): Список email для копии ("Копия") (по умолчанию None).

        Возвращает:
            dict: JSON ответ от сервера с данными созданной заявки.
        """
        title = f"Обновление BoardMaps {version} SaaS"
        
        description_html = f"""
        <body style="margin: 0; padding: 0;">
            <font style="color: #2f2f2f; font-family: Arial, sans-serif; font-size: 14px; line-height: 16px;" align="justify">
                <table border="0" align="left" width="100%" height="auto" cellpadding="0" cellspacing ="0" background-size= "contain" background-repeat="no-repeat" background-position="left">
                <tr>
                <td>
                    <table style="border-collapse:collapse;" border="0" width="95%" cellpadding="0" cellspacing ="0" align="center">
                        <tr>
                            <td>
                                Уважаемый клиент!
                                <br><br>
                                <p>На {date_time} по МСК запланированы работы по обновлению BoardMaps до версии <b>{version}</b>.</p>
                                <p>Сервис будет временно недоступен.</p>
                                <br>
                                <p>Пожалуйста, сообщите нам в ответном письме, если для вас важен доступ к сервису в указанное время.</p>
                                <br>
                            </td>
                        </tr>
                    </td>
                </tr>
                </table>
            </font>
        </body>
        """
        
        return self._create_ticket(title, description_html, user_email, cc_emails)

    def _create_ticket(self, title, description, user_email, cc_emails=None):
        """
        Создает заявку на основе предоставленных данных.

        Параметры:
            title (str): Заголовок заявки.
            description (str): Описание заявки в формате HTML.
            user_email (str): Email основного получателя заявки ("Кому").
            cc_emails (list): Список email для копии ("Копия") (по умолчанию None).

        Возвращает:
            dict: JSON ответ от сервера с данными созданной заявки.

        Исключения:
            Exception: Возникает, если создание заявки не удалось после всех попыток.
        """
        data = {
            'title': title,
            'description': description,
            'type_id': 9,
            'status_id': "7",
            'user_email': user_email,
            'cc': cc_emails,
            "custom_fields": {
                "2": {"1": "28"}, # Указываем значение "Запрос к клиенту"
                3: 15 # Указываем значение "BoardMaps Core"
            }
        }
        
        attempt = 0
        while attempt < self.retries:
            try:
                response = self.session.post(f"{self.api_url}/tickets/", json=data, timeout=self.timeout)
                response.raise_for_status()
                scripts_info_logger.info(f"Успешно создана заявка для {user_email} с копиями {cc_emails}")
                return response.json()
            except RequestException as error_message:
                scripts_error_logger.error(f"Попытка {attempt + 1} не удалась для {user_email}: {str(error_message)}")
                attempt += 1
                time.sleep(2 ** attempt)  # Экспоненциальная задержка
                if attempt == self.retries:
                    raise Exception(f"Ошибка при создании заявки после {self.retries} попыток: {str(error_message)}")

if __name__ == "__main__":
    helpdesk_client = HelpDeskEddyClient()
    version = "3.16"
    to_email = "oleg.eliseev@boardmaps.ru"
    cc_emails = ["oleg.eliseev@boardmaps.com"]
    date_time = "11.08.2024 в 18:00"
    helpdesk_client.send_service_request(version, to_email, cc_emails)
    helpdesk_client.send_saas_notification(version, to_email, date_time, cc_emails)
