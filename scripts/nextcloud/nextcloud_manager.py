import requests
import os
import time
import logging
import xml.etree.ElementTree as ET
import urllib.parse
from logger.log_config import setup_logger, get_abs_log_path


scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

# Скрыть вывод DEBUG для библиотеки requests и urllib3
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class NextcloudManager:
    def __init__(self, nextcloud_url, username, password, retry_delay=5, max_retries=5, timeout=30):
        self.nextcloud_url = nextcloud_url
        self.username = username
        self.password = password
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.timeout = timeout

    def create_folder(self, folder_path):
        try:
            parts = folder_path.strip('/').split('/')
            for i in range(1, len(parts) + 1):
                sub_folder_path = '/'.join(parts[:i])
                url = f"{self.nextcloud_url}/remote.php/dav/files/{self.username}/{sub_folder_path}"
                time.sleep(self.retry_delay)
                response = requests.request("MKCOL", url, auth=(self.username, self.password), timeout=self.timeout)
                if response.status_code == 201:
                    scripts_info_logger.info('Папка %s успешно создана на Nextcloud.', sub_folder_path)
                elif response.status_code == 405:
                    scripts_info_logger.info(f"Папка {sub_folder_path} уже существует на Nextcloud.")
                elif response.status_code != 409:
                    error_msg = f"Ошибка при создании папки {sub_folder_path} на Nextcloud. Код статуса: {response.status_code}, Текст ошибки: {response.text}"
                    scripts_error_logger.error(error_msg)
                    raise Exception(error_msg)
        except requests.exceptions.RequestException as error:
            scripts_error_logger.error("Произошла ошибка: %s", error)
            raise
        except IOError as error:
            scripts_error_logger.error("Ошибка ввода-вывода: %s", error)
            raise
        except Exception as error:
            scripts_error_logger.error(f"Произошла общая ошибка создания папки на Nextcloud: {str(error)}")
            raise

    def upload_file(self, local_file_path, remote_file_path):
        url = f"{self.nextcloud_url}/remote.php/dav/files/{self.username}/{remote_file_path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self.retry_delay)
                with open(local_file_path, "rb") as file:
                    response = requests.put(url, data=file, auth=(self.username, self.password), timeout=self.timeout)
                if response.status_code == 201:
                    scripts_info_logger.info("Файл %s успешно загружен на Nextcloud.", local_file_path)
                    return True
                else:
                    scripts_error_logger.error("Ошибка при загрузке файла %s на Nextcloud. Код статуса: %s, Текст ошибки: %s", local_file_path, response.status_code, response.text)
                    return False
            except requests.exceptions.RequestException as e:
                scripts_error_logger.error(f"Попытка {attempt}/{self.max_retries} не удалась для файла {local_file_path}: {str(e)}")
                if attempt == self.max_retries:
                    raise
                time.sleep(self.retry_delay)
        return False
    
    def move_internal_folders(self, src_dir, dest_dir):
        """
        Функция для перемещения внутренних папок из одной директории в другую на Nextcloud.

        :param src_dir: Исходная директория.
        :param dest_dir: Целевая директория.
        """
        ns = {"d": "DAV:"}
        src_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + src_dir.strip("/")
        dest_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + dest_dir.strip("/")

        # Получение списка элементов исходной директории с использованием метода propfind_request
        xml_data = self.propfind_request(src_url, depth=1)

        # Формирование списка путей элементов исходной директории
        item_paths = [
            e.find("d:href", ns).text for e in xml_data.findall(".//d:response", ns)
        ]

        # Обработка и перемещение внутренних папок исходной директории
        for item_path in item_paths[1:]:
            item_name = urllib.parse.unquote(item_path.split("/")[-2])
            item_src_url = src_url + "/" + urllib.parse.quote(item_name)
            item_dest_url = dest_url + "/" + urllib.parse.quote(item_name)

            headers = {
                "Destination": item_dest_url.encode("utf-8", "ignore").decode("latin-1"),
                "Overwrite": "F",
            }
            try:
                time.sleep(self.retry_delay)
                response = requests.request("MOVE", item_src_url, headers=headers, auth=(self.username, self.password), timeout=self.timeout)
            except requests.exceptions.RequestException as error:
                scripts_error_logger.error("Ошибка при выполнении запроса: %s", error)
                raise Exception(f"Ошибка при выполнении запроса: {error}")
        
            if response.status_code == 201:
                scripts_info_logger.info('Элемент %s/%s успешно перемещен в %s/%s на Nextcloud.', src_dir, item_name, dest_dir, item_name)
            elif response.status_code == 404:
                scripts_error_logger.error("Элемент %s/%s не найден на Nextcloud.", src_dir, item_name)
            elif response.status_code == 412:
                scripts_error_logger.error(f"Элемент {dest_dir}/{item_name} уже существует на Nextcloud.")
            else:
                scripts_error_logger.error("Ошибка при перемещении элемента %s/%s на Nextcloud. Код статуса: %s", src_dir, item_name, response.status_code)
                scripts_error_logger.error("Содержимое ответа сервера: %s", response.text)

    def propfind_request(self, url, depth=0):
        """
        Функция выполняет PROPFIND-запрос к серверу WebDAV (Nextcloud).
        PROPFIND-запрос используется для получения свойств и структуры коллекций или ресурсов.

        Args:
            url (str): URL-адрес, к которому отправляется запрос.
            depth (int, optional): Глубина просмотра. 0 для текущего ресурса, 1 для ресурса и его непосредственных дочерних элементов. По умолчанию 0.

        Returns:
            xml.etree.ElementTree.Element: Возвращает объект ElementTree с данными, полученными в результате PROPFIND-запроса.

        Raises:
            Exception: Возникает, если код статуса ответа не равен 207.
        """
        headers = {
            "Depth": str(depth),
            "Content-Type": "application/xml",
        }

        body = """<?xml version="1.0" encoding="utf-8" ?>
            <d:propfind xmlns:d="DAV:">
                <d:prop>
                    <d:resourcetype/>
                </d:prop>
            </d:propfind>
        """

        try:
            time.sleep(self.retry_delay)
            response = requests.request("PROPFIND", url, headers=headers, data=body, auth=(self.username, self.password), timeout=self.timeout)
        except requests.exceptions.RequestException as error:
            print(f"Ошибка при выполнении запроса: {error}")
            scripts_error_logger.error("Ошибка при выполнении запроса: %s", error)
            raise Exception(f"Ошибка при выполнении запроса: {error}")

        if response.status_code != 207:
            scripts_error_logger.error("Ошибка при выполнении PROPFIND-запроса. Код статуса: %s, Текст ошибки: %s", response.status_code, response.text)
            raise Exception(f"Ошибка при выполнении PROPFIND-запроса. Код статуса: {response.status_code}, Текст ошибки: {response.text}")

        xml_data = ET.fromstring(response.content)

        return xml_data
