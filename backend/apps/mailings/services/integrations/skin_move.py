import os
import json
import subprocess
import tempfile
import shutil
import shlex
from urllib.parse import quote
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from apps.clients.models import Client, TechnicalInfo
from apps.mailings.services.integrations.nextcloud import NextcloudManager
from apps.mailings.services.integrations.yandex_disk import upload_to_nextcloud
from apps.mailings.services.utils.config import get_config_path
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = get_config_path()
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)

USERNAME = data["FILE_SHARE"]["USERNAME"]
PASSWORD = data["FILE_SHARE"]["PASSWORD"]
DOMAIN = data["FILE_SHARE"]["DOMAIN"]
SMB_SERVER = data["FILE_SHARE"]["SMB_SERVER"]
SHARE_PATH = f"//{SMB_SERVER}.{DOMAIN}/data/"

NEXTCLOUD_URL = data["NEXT_CLOUD"]["URL"]
NEXTCLOUD_USERNAME = data["NEXT_CLOUD"]["USER"]
NEXTCLOUD_PASSWORD = data["NEXT_CLOUD"]["PASSWORD"]

nextcloud_module = NextcloudManager(NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)


def get_clients_list(version, component_type):
    major_version = version.split(".")[0]
    skin_field = "technical_info__skins_ios" if component_type == "ipad" else "technical_info__skins_web"
    clients = Client.objects.filter(**{skin_field: True}, contact_status=True, technical_info__server_version__startswith=major_version)
    return list(clients.values("client_name", "short_name"))


@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=10), retry=retry_if_exception_type(subprocess.CalledProcessError))
def download_files(release_path, skin_filename):
    temp_dir = tempfile.mkdtemp()
    safe_release_path = f'"{release_path}"'
    safe_skin_filename = f'"{skin_filename}"'
    smbclient_command = (
        f"smbclient {shlex.quote(SHARE_PATH)} -U {shlex.quote(DOMAIN)}/{shlex.quote(USERNAME)}%{shlex.quote(PASSWORD)} "
        f"-c 'prompt; cd {safe_release_path}; get {safe_skin_filename}'"
    )
    result = subprocess.run(smbclient_command, shell=True, cwd=temp_dir, capture_output=True, text=True)
    if "NT_STATUS_OBJECT_NAME_NOT_FOUND" in result.stdout:
        logger.warning('Файл %s отсутствует в %s, клиент пропущен.', skin_filename, release_path)
        return "NO_FILE"
    if result.returncode != 0:
        logger.error('Ошибка скачивания %s: %s', skin_filename, result.stderr.strip() or 'Неизвестная ошибка')
        return "ERROR"
    logger.info('Файл %s успешно скачан в %s', skin_filename, temp_dir)
    return temp_dir


def move_old_boardmaps_folder(client_name, folder_type, version):
    try:
        client_directory = f"{client_name}/1. Кастомизация/"
        old_versions_path = f"{client_name}/1. Кастомизация/Старые версии/"
        if not nextcloud_module.folder_exists(old_versions_path):
            nextcloud_module.create_folder(old_versions_path)
        folders = nextcloud_module.list_folder(client_directory)
        old_boardmaps_prefix = f"BoardMaps {folder_type} "
        for folder in folders.splitlines():
            if folder.startswith(old_boardmaps_prefix):
                old_boardmaps_path = f"{client_directory}{folder}"
                destination_path = f"{old_versions_path}{folder}"
                nextcloud_module.move_folder(old_boardmaps_path, destination_path)
                logger.info('Перемещена старая папка "%s" в "%s"', folder, old_versions_path)
                return None
        logger.info('Нет старых папок "BoardMaps %s ..." для перемещения.', folder_type)
    except Exception as error:
        error_msg = f'Ошибка при перемещении старой папки "BoardMaps {folder_type} {version}": {error}'
        logger.error(error_msg)
        return error_msg


def move_skins_and_manage_share(version, component_type):
    if component_type not in ["ipad", "web"]:
        raise ValueError("Неверный тип скинов. Доступны 'ipad' и 'web'.")
    folder_type = "iPad" if component_type == "ipad" else "Server"
    try:
        clients_list = get_clients_list(version, component_type)
        logger.info('Найдено клиентов с %s-скинами (версия %s): %s', component_type, version, len(clients_list))
        if not clients_list:
            logger.error('Нет клиентов с %s-скинами для версии %s!', component_type, version)
            return "NO_CLIENTS"
        for client in clients_list:
            short_name = client.get("short_name")
            full_name = client.get("client_name")
            if not short_name or not full_name:
                logger.warning('Пропускаем клиента без имени: %s', client)
                continue
            logger.info('Обрабатываем клиента: "%s" (%s)', full_name, folder_type)
            try:
                release_path = f"Releases/[{folder_type}-skins]/{version}"
                skin_filename = f"{short_name}.zip" if component_type == "ipad" else f"{short_name}_theme.{version}.json.zip"
                temp_dir = download_files(release_path, skin_filename)
                if temp_dir == "NO_FILE":
                    continue
                elif temp_dir == "ERROR":
                    continue
                client_folder_path = f"{short_name}/1. Кастомизация/BoardMaps {folder_type} {version}"
                if not nextcloud_module.folder_exists(client_folder_path):
                    move_old_boardmaps_folder(short_name, folder_type, version)
                nextcloud_module.create_folder(client_folder_path)
                local_skin_path = os.path.join(temp_dir, skin_filename)
                remote_skin_path = quote(f"{client_folder_path}/{skin_filename}", safe="/")
                try:
                    upload_to_nextcloud(local_skin_path, remote_skin_path, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
                    os.remove(local_skin_path)
                except Exception as e:
                    logger.error('Ошибка загрузки %s на NextCloud, клиент %s пропущен: %s', skin_filename, full_name, e)
                    continue
            except Exception as error_message:
                error_msg = f'Ошибка обработки клиента "{full_name}": {error_message}'
                logger.error(error_msg)
                return error_msg
        logger.info('Перемещение %s-скинов успешно завершено', folder_type)
        return None
    except Exception as error_message:
        error_msg = f'Произошла ошибка при перемещении {folder_type}-скинов: {error_message}'
        logger.error(error_msg)
        return error_msg
