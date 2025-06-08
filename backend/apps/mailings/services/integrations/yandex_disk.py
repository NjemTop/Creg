import os
import tempfile
import requests
import logging
from urllib.parse import quote
from django.conf import settings
from logger.log_config import setup_logger, get_abs_log_path

scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


class YandexDiskManager:
    def __init__(self, access_token, retry_delay=5, max_retries=5, timeout=30):
        self.access_token = access_token
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.timeout = timeout

    def get_files_list(self, folder_path):
        headers = {"Authorization": f"OAuth {self.access_token}"}
        url = f"https://cloud-api.yandex.net/v1/disk/resources?path={quote(folder_path)}&limit=100"
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
        except requests.exceptions.RequestException as error:
            scripts_error_logger.error("Ошибка при выполнении запроса: %s", error)
            return []
        if response.status_code == 200:
            return response.json()['_embedded']['items']
        scripts_error_logger.error("Ошибка при получении списка файлов. Код статуса: %s", response.status_code)
        return []

    def download_file(self, download_url, local_file_path):
        for attempt in range(1, self.max_retries + 1):
            try:
                with open(local_file_path, "wb") as file:
                    resp = requests.get(download_url, timeout=self.timeout)
                    resp.raise_for_status()
                    file.write(resp.content)
                return True
            except (requests.exceptions.RequestException, IOError) as e:
                scripts_error_logger.error("Попытка %s/%s не удалась для файла %s: %s", attempt, self.max_retries, local_file_path, e)
                if attempt == self.max_retries:
                    raise
        return False


def upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, username, password):
    url = f"{nextcloud_url}/remote.php/dav/files/{username}/{quote(remote_file_path)}"
    with open(local_file_path, "rb") as file:
        resp = requests.put(url, data=file, auth=(username, password), timeout=30)
    if resp.status_code == 201:
        scripts_info_logger.info("Файл %s успешно загружен на Nextcloud.", local_file_path)
    else:
        scripts_error_logger.error("Ошибка при загрузке файла %s на Nextcloud: %s", local_file_path, resp.text)


def determine_product_type(folder_path):
    if "iPad" in folder_path or "iPhone" in folder_path:
        return "iOS_iPadOS 3.0" if "3.0" in folder_path else "iOS_iPadOS 2.0"
    if "Android" in folder_path:
        return "Android 3.0" if "3.0" in folder_path else "Android 2.0"
    if "Server" in folder_path or "BoardMaps 3.0" in folder_path:
        return "Server 3.0" if "BoardMaps 3.0" in folder_path else "Server 2.0"
    return "Неизвестный тип"


def get_relevant_paths(release_type, folder_paths, server_version=None, ipad_version=None, android_version=None):
    relevant_paths = []
    base_release_type = release_type.replace('Android', '').replace('iPad', '')
    if base_release_type in folder_paths:
        if server_version and "server" in folder_paths[base_release_type]:
            relevant_paths.extend(folder_paths[base_release_type]["server"])
        if ipad_version and "ipad" in folder_paths[base_release_type]:
            relevant_paths.extend(folder_paths[base_release_type]["ipad"])
        if android_version and "android" in folder_paths[base_release_type]:
            relevant_paths.extend(folder_paths[base_release_type]["android"])
    else:
        raise KeyError(f"Ключ '{base_release_type}' отсутствует в folder_paths")
    return relevant_paths


def update_local_documentation(access_token, folder_paths, release_type, language, server_version=None, ipad_version=None, android_version=None):
    yandex_manager = YandexDiskManager(access_token)
    language = language.upper()
    attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', language)
    relevant_paths = get_relevant_paths(release_type, folder_paths, server_version, ipad_version, android_version)
    for template in relevant_paths:
        if 'Android' in template:
            version_info = android_version
        elif 'iPad' in template or 'iPhone' in template or 'iOS' in template:
            version_info = ipad_version
        else:
            version_info = server_version
        folder_path = template.format(version_info=version_info, language=language)
        items = yandex_manager.get_files_list(folder_path)
        if items is not None:
            for item in items:
                if ('U80.0.0 Список изменений' in item['name'] or 'Release notes' in item['name']) and (
                        (server_version and f'{server_version}.pdf' in item['name']) or
                        (ipad_version and f'{ipad_version}.pdf' in item['name']) or
                        (android_version and f'{android_version}.pdf' in item['name'])):
                    local_file_path = os.path.join(attachments_dir, item['name'])
                    try:
                        with open(local_file_path, "wb") as file:
                            response = requests.get(item['file'], timeout=30)
                            response.raise_for_status()
                            file.write(response.content)
                        scripts_info_logger.info(f"Скачан новый файл: {item['name']}")
                    except (requests.exceptions.RequestException, IOError) as error:
                        scripts_error_logger.error(f"Ошибка при скачивании файла {item['name']}: {error}")
        else:
            scripts_error_logger.error(f"Не удалось получить список файлов для пути: {folder_path}")

