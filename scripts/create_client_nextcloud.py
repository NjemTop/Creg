import requests
import base64
import logging
from logger.log_config import setup_logger, get_abs_log_path
from time import sleep
from requests.exceptions import RequestException


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts', get_abs_log_path('scripts_info.log'), logging.INFO)


# Константы
FOLDER_IDS = ['62', '86']  # Айди папок "1. Актуальный релиз" и "2. Предыдущий релиз"
DEFAULT_PERMISSIONS_FOLDER = 7  # Права на чтение в две шарные папки "1. Актуальный релиз" и "2. Предыдущий релиз"
RETRY_ATTEMPTS = 3  # Количество попыток для повторения запроса

class NextCloudManager:
    def __init__(self, base_url, username, password):
        """
        Инициализация менеджера NextCloud.

        :param base_url: базовый URL NextCloud
        :param username: имя пользователя для авторизации
        :param password: пароль для авторизации
        """
        self.base_url = base_url
        self.headers = {
            'OCS-APIRequest': 'true',
            'Authorization': 'Basic ' + base64.b64encode(f"{username}:{password}".encode('ascii')).decode('ascii'),
            'User-Agent': 'MyApp/1.0',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.folder_ids = FOLDER_IDS
    
    def _send_request(self, url, payload):
        """
        Отправляет HTTP POST-запрос и возвращает ответ.

        :param url: URL для отправки запроса
        :param payload: Данные для отправки
        :return: Ответ сервера или None в случае ошибки
        """
        for _ in range(RETRY_ATTEMPTS):  # Попытки повторения запроса
            try:
                response = requests.post(url, headers=self.headers, data=payload)
                
                if response.status_code >= 200 and response.status_code < 300:
                    # HTTP статусы 2xx означают успешное выполнение запроса
                    return response
                elif response.status_code == 400:
                    scripts_error_logger.error("Некорректный запрос: параметры запроса недопустимы.")
                elif response.status_code == 401:
                    scripts_error_logger.error("Ошибка авторизации: недопустимые учетные данные.")
                elif response.status_code == 403:
                    scripts_error_logger.error("Ошибка доступа: у вас нет прав для выполнения этого действия.")
                elif response.status_code == 404:
                    scripts_error_logger.error("Ресурс не найден.")
                else:
                    scripts_error_logger.error(f"Неизвестная ошибка: {response.status_code}")

                sleep(3)  # Задержка перед повторной попыткой

            except RequestException as error_message:
                scripts_error_logger.error(f"Ошибка запроса: {error_message}")
                sleep(3)  # Задержка перед повторной попыткой

        return None  # Возвращаем None после всех неудачных попыток
    
    def create_account(self, client_name, account_name):
        """
        Создает учетную запись пользователя в NextCloud.
        
        :param client_name: полное имя клиента
        :param account_name: учётная запись клиента
        :return: True если успешно, иначе False
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/users"
        payload = {'userid': account_name, 'password': f"{account_name}321", 'displayname': client_name}
        response = self._send_request(url, payload)
        if response and response.status_code == 200:
            print(f"Успешно создана учетная запись NextCloud для {client_name}")
            scripts_info_logger.info(f"Успешно создана учетная запись NextCloud для {client_name}")
            return True
        else:
            print(f"Не удалось создать учетную запись NextCloud для {client_name}")
            scripts_error_logger.error(f"Не удалось создать учетную запись NextCloud для {client_name}")
            return False

    def create_group(self, group_name):
        """
        Создает группу в NextCloud.
        
        :param group_name: имя группы клиента
        :return: True если успешно, иначе False
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/groups"
        payload = {'groupid': group_name}
        response = self._send_request(url, payload)
        if response and response.status_code == 200:
            print(f"Группа NextCloud успешно создана: {group_name}")
            scripts_info_logger.info(f"Группа NextCloud успешно создана: {group_name}")
            return True
        else:
            print(f"Не удалось создать группу NextCloud: {group_name}")
            scripts_error_logger.error(f"Не удалось создать группу NextCloud: {group_name}")
            return False

    def add_user_to_group(self, user_name, group_name):
        """
        Добавляет пользователя в группу в NextCloud.

        :param user_name: учётная запись клиента
        :param group_name: имя группы клиента
        :return: True если успешно, иначе False
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/users/{user_name}/groups"
        payload = {'groupid': group_name}
        response = self._send_request(url, payload)
        if response and response.status_code == 200:
            print(f"Успешно добавлено {user_name} в группу NextCloud {group_name}")
            scripts_info_logger.info(f"Успешно добавлено {user_name} в группу NextCloud {group_name}")
            return True
        else:
            print(f"Ошибка добавления {user_name} в группу NextCloud {group_name}")
            scripts_error_logger.error(f"Ошибка добавления {user_name} в группу NextCloud {group_name}")
            return False
    
    def add_group_to_folder_and_set_permissions(self, folder_id, group_name):
        """
        Добавляет группу к папке и устанавливает разрешения.

        :param folder_id: id папок для предоставления доступа
        :param group_name: имя группы клиента
        :return: True если успешно, иначе False
        """
        url_add_group = f"{self.base_url}/apps/groupfolders/folders/{folder_id}/groups"
        payload_add_group = {'group': group_name}
        response_add_group = self._send_request(url_add_group, payload_add_group)
        if not response_add_group:
            return False

        url_set_perms = f"{self.base_url}/apps/groupfolders/folders/{folder_id}/groups/{group_name}"
        payload_set_perms = {'permissions': DEFAULT_PERMISSIONS_FOLDER}
        response_set_perms = self._send_request(url_set_perms, payload_set_perms)
        if response_set_perms and response_set_perms.status_code == 200:
            print(f"Успешно установлены разрешения для группы {group_name} в папке {folder_id}")
            scripts_info_logger.info(f"Успешно установлены разрешения для группы {group_name} в папке {folder_id}")
            return True
        else:
            print(f"Не удалось установить разрешения для группы {group_name} в папке {folder_id}")
            scripts_error_logger.error(f"Не удалось установить разрешения для группы {group_name} в папке {folder_id}")
            return False

    def execute_all(self, client_name, account_name, group_name):
        """Выполняет все задачи по созданию пользователя, группы и разрешений."""
        if not self.create_account(client_name, account_name):
            return
        if not self.create_group(group_name):
            return
        if not self.add_user_to_group(account_name, group_name):
            return
        for folder_id in self.folder_ids:
            if not self.add_group_to_folder_and_set_permissions(folder_id, group_name):
                return

if __name__ == "__main__":
    manager = NextCloudManager("https://cloud.boardmaps.ru", "ncloud", "G6s6kWaZWyOC0oLt")
    manager.execute_all("Международная контейнерная логистика (МКЛ)", "mkl", "mkl")
