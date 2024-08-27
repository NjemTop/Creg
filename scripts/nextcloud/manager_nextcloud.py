import requests
import base64
import logging
from logger.log_config import setup_logger, get_abs_log_path
from time import sleep
from requests.exceptions import RequestException


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


# Константы
FOLDER_IDS = ['62', '86']  # Айди папок "1. Актуальный релиз" и "2. Предыдущий релиз"
DEFAULT_PERMISSIONS_FOLDER = 7  # Права на чтение в две шарные папки "1. Актуальный релиз" и "2. Предыдущий релиз"
RETRY_ATTEMPTS = 3  # Количество попыток для повторения запроса

class NextCloudManager:
    def __init__(self, base_url, username, password):
        """
        Инициализация менеджера NextCloud.

        Args:
            base_url (str): базовый URL NextCloud.
            username (str): имя пользователя для авторизации.
            password (str): пароль для авторизации.
        """
        self.base_url = base_url
        self.headers = {
            'OCS-APIRequest': 'true',
            'Authorization': 'Basic ' + base64.b64encode(f"{username}:{password}".encode('ascii')).decode('ascii'),
            'User-Agent': 'MyApp/1.0',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self.folder_ids = FOLDER_IDS
    
    def _send_request(self, method, url, payload=None):
        """
        Отправляет HTTP запрос и возвращает ответ.

        Args:
            method (str): HTTP метод, например 'GET', 'POST', 'DELETE'.
            url (str): полный URL для запроса.
            payload (dict, optional): тело запроса для методов POST, PATCH и DELETE.

        Returns:
            requests.Response or None: объект ответа requests, если запрос успешен; None, если запрос не удался.
        """
        for _ in range(RETRY_ATTEMPTS):  # Попытки повторения запроса
            try:
                response = requests.request(method, url, headers=self.headers, data=payload)
                
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
        
        Args:
            client_name (str): полное имя клиента.
            account_name (str): учётная запись клиента.
        Returns:
            bool: True если успешно, иначе False.
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/users"
        payload = {'userid': account_name, 'password': f"{account_name}321", 'displayname': client_name}
        response = self._send_request('POST', url, payload)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Успешно создана учетная запись NextCloud для {client_name}")
            scripts_info_logger.info(f"Response: {response.text}")
            return True
        else:
            scripts_error_logger.error(f"Не удалось создать учетную запись NextCloud для {client_name}")
            return False

    def create_group(self, group_name):
        """
        Создает группу в NextCloud.
        
        Args:
            group_name (str): имя группы клиента.
        Returns:
            bool: True если успешно, иначе False.
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/groups"
        payload = {'groupid': group_name}
        response = self._send_request('POST', url, payload)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Группа NextCloud успешно создана: {group_name}")
            return True
        else:
            scripts_error_logger.error(f"Не удалось создать группу NextCloud: {group_name}")
            return False

    def add_user_to_group(self, user_name, group_name):
        """
        Добавляет пользователя в группу в NextCloud.

        Args:
            user_name (str): учётная запись клиента.
            group_name (str): имя группы клиента.
        Returns:
            bool: True если успешно, иначе False.
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/users/{user_name}/groups"
        payload = {'groupid': group_name}
        response = self._send_request('POST', url, payload)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Успешно добавлено {user_name} в группу NextCloud {group_name}")
            return True
        else:
            scripts_error_logger.error(f"Ошибка добавления {user_name} в группу NextCloud {group_name}")
            return False
    
    def add_group_to_folder_and_set_permissions(self, folder_id, group_name):
        """
        Добавляет группу к папке и устанавливает разрешения.

        Args:
            folder_id (int): id папок для предоставления доступа.
            group_name (str): имя группы клиента.
        Returns:
            bool: True если успешно, иначе False.
        """
        url_add_group = f"{self.base_url}/apps/groupfolders/folders/{folder_id}/groups"
        payload_add_group = {'group': group_name}
        response_add_group = self._send_request('POST', url_add_group, payload_add_group)
        if not response_add_group:
            return False

        url_set_perms = f"{self.base_url}/apps/groupfolders/folders/{folder_id}/groups/{group_name}"
        payload_set_perms = {'permissions': DEFAULT_PERMISSIONS_FOLDER}
        response_set_perms = self._send_request('POST', url_set_perms, payload_set_perms)
        if response_set_perms and response_set_perms.status_code == 200:
            scripts_info_logger.info(f"Успешно установлены разрешения для группы {group_name} в папке {folder_id}")
            return True
        else:
            scripts_error_logger.error(f"Не удалось установить разрешения для группы {group_name} в папке {folder_id}")
            return False
    
    def create_group_folder(self, folder_name):
        """
        Создает папку группы в NextCloud.

        Args:
            folder_name (str): название папки для создания.

        Returns:
            int or None: ID созданной папки если успешно; None в противном случае.
        """
        url = f"{self.base_url}/ocs/v2.php/apps/groupfolders/folders"
        payload = {'mountpoint': folder_name}
        response = self._send_request('POST', url, payload)
        if response and response.status_code == 200:
            folder_id = response.json().get('data', {}).get('id')
            scripts_info_logger.info(f"Папка {folder_name} успешно создана с ID {folder_id}.")
            return folder_id
        scripts_error_logger.error(f"Не удалось создать папку {folder_name}.")
        return None

    def set_permissions_for_folder(self, folder_id, group_name, permissions):
        """
        Устанавливает разрешения для папки группы в NextCloud.

        Args:
            folder_id (int): ID папки.
            group_name (str): имя группы для назначения разрешений.
            permissions (int): числовой код разрешений (7 для чтения).

        Returns:
            bool: True, если разрешения успешно установлены; False в противном случае.
        """
        url = f"{self.base_url}/ocs/v2.php/apps/groupfolders/folders/{folder_id}/acl"
        payload = {'groupid': group_name, 'permissions': permissions}
        response = self._send_request('POST', url, payload)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Разрешения для группы {group_name} успешно установлены на папке {folder_id}.")
            return True
        scripts_error_logger.error(f"Не удалось установить разрешения для группы {group_name} на папке {folder_id}.")
        return False

    def execute_all(self, client_name, account_name, group_name):
        """Выполняет все задачи по созданию пользователя, группы и разрешений."""
        if not self.create_account(client_name, account_name):
            return False
        if not self.create_group(group_name):
            return False
        if not self.add_user_to_group(account_name, group_name):
            return False
        for folder_id in self.folder_ids:
            if not self.add_group_to_folder_and_set_permissions(folder_id, group_name):
                return False
        folder_id = self.create_group_folder(account_name)
        if folder_id is None:
            return False
        if not self.set_permissions_for_folder(folder_id, group_name, 7):
            return False
        return True
    
    def delete_user(self, user_name):
        """
        Удаляет пользователя из NextCloud.

        Args:
            user_name (str): имя учетной записи пользователя для удаления.

        Returns:
            bool: True, если удаление успешно; False в противном случае.
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/users/{user_name}"
        response = self._send_request('DELETE', url)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Пользователь {user_name} успешно удалён.")
            return True
        scripts_error_logger.error(f"Не удалось удалить пользователя {user_name}.")
        return False

    def delete_group(self, group_name):
        """
        Удаляет группу из NextCloud.

        Args:
            group_name (str): имя группы для удаления.

        Returns:
            bool: True, если удаление успешно; False в противном случае.
        """
        url = f"{self.base_url}/ocs/v1.php/cloud/groups/{group_name}"
        response = self._send_request('DELETE', url)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Группа {group_name} успешно удалена.")
            return True
        scripts_error_logger.error(f"Не удалось удалить группу {group_name}.")
        return False

    def remove_group_from_folder(self, folder_id, group_name):
        """
        Удаляет группу из папки и снимает все права доступа.

        Args:
            folder_id (int): ID папки, из которой нужно удалить группу.
            group_name (str): имя группы для удаления.

        Returns:
            bool: True, если удаление успешно; False в противном случае.
        """
        url = f"{self.base_url}/apps/groupfolders/folders/{folder_id}/groups/{group_name}"
        response = self._send_request('DELETE', url)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Группа {group_name} удалена из папки {folder_id}.")
            return True
        scripts_error_logger.error(f"Не удалось удалить группу {group_name} из папки {folder_id}.")
        return False
    
    def get_folder_id_by_name(self, folder_name):
        """
        Получает ID папки по её названию.

        Args:
            folder_name (str): Название папки.

        Returns:
            int or None: ID папки если найдена; None в противном случае.
        """
        url = f"{self.base_url}/ocs/v2.php/apps/groupfolders/folders"
        response = self._send_request('GET', url)
        if response and response.status_code == 200:
            folders = response.json().get('ocs', {}).get('data', [])
            for folder in folders:
                if folder.get('mount_point') == folder_name:
                    return folder.get('id')
            scripts_info_logger.info(f"Папка {folder_name} не найдена.")
        else:
            scripts_error_logger.error("Не удалось получить список папок.")
        return None
    
    def delete_group_folder(self, folder_id):
        """
        Удаляет папку группы из NextCloud.

        Args:
            folder_id (int): ID папки для удаления.

        Returns:
            bool: True, если папка успешно удалена; False в противном случае.
        """
        url = f"{self.base_url}/ocs/v2.php/apps/groupfolders/folders/{folder_id}"
        response = self._send_request('DELETE', url)
        if response and response.status_code == 200:
            scripts_info_logger.info(f"Папка с ID {folder_id} успешно удалена.")
            return True
        scripts_error_logger.error(f"Не удалось удалить папку с ID {folder_id}.")
        return False

    def execute_deletion(self, user_name, group_name):
        """
        Выполняет полное удаление пользователя, группы и доступов.

        Args:
            user_name (str): имя учетной записи пользователя для удаления.
            group_name (str): имя группы для удаления.

        Returns:
            bool: True, если все операции удаления успешны; False в противном случае.
        """
        if not self.delete_user(user_name):
            return False
        if not self.delete_group(group_name):
            return False
        for folder_id in FOLDER_IDS:
            if not self.remove_group_from_folder(folder_id, group_name):
                return False
        folder_id = self.get_folder_id_by_name(group_name)
        if not self.delete_group_folder(folder_id):
            return False
        else:
            scripts_error_logger.error(f"Не удалось найти папку с названием {folder_name} для удаления.")
            return False
        return True

if __name__ == "__main__":
    manager = NextCloudManager("https://cloud.boardmaps.ru", "ncloud", "пароль")
    manager.execute_all("Тестовый клиент", "testclient", "testclient")
    manager.execute_deletion('testclient', 'testclient')
