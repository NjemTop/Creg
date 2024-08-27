import requests
from urllib.parse import quote
import tempfile
import os
import time
import traceback
import logging
from logger.log_config import setup_logger, get_abs_log_path


scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

# Скрываем вывод DEBUG для библиотеки requests и urllib3
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class YandexDiskManager:
    def __init__(self, access_token, retry_delay=5, max_retries=5, timeout=30):
        self.access_token = access_token
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.timeout = timeout

    def get_files_list(self, folder_path):
        headers = {
            "Authorization": f"OAuth {self.access_token}"
        }
        encoded_folder_path = quote(folder_path)
        url = f"https://cloud-api.yandex.net/v1/disk/resources?path={encoded_folder_path}&limit=100"
        try:
            time.sleep(self.retry_delay)
            response = requests.get(url, headers=headers, timeout=self.timeout)
        except requests.exceptions.RequestException as error:
            scripts_error_logger.error("Ошибка при выполнении запроса: %s", error)
            return []
        
        if response.status_code == 200:
            response_data = response.json()
            items = response_data['_embedded']['items']
            return items
        else:
            scripts_error_logger.error("Ошибка при получении списка файлов. Код статуса: %s, Текст ошибки: %s", response.status_code, response.text)
            return []

    def download_file(self, download_url, local_file_path):
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self.retry_delay)
                with open(local_file_path, "wb") as file:
                    response = requests.get(download_url, timeout=self.timeout)
                    response.raise_for_status()
                    file.write(response.content)
                return True
            except (requests.exceptions.RequestException, IOError) as e:
                scripts_error_logger.error(f"Попытка {attempt}/{self.max_retries} не удалась для файла {local_file_path}: {str(e)}")
                if attempt == self.max_retries:
                    raise
                time.sleep(self.retry_delay)
        return False
