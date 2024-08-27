import os
import time
from django.conf import settings
import tempfile
import requests
from scripts.yandex.yandex_disk_manager import YandexDiskManager
from scripts.nextcloud.nextcloud_manager import NextcloudManager
import logging
from logger.log_config import setup_logger, get_abs_log_path, log_errors


scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


def determine_product_type(folder_path):
    """
    Определяет тип продукта на основе пути к папке.
    """
    if "iPad" in folder_path or "iPhone" in folder_path:
        if "3.0" in folder_path:
            return "iOS_iPadOS 3.0"
        else:
            return "iOS_iPadOS 2.0"
    elif "Android" in folder_path:
        if "3.0" in folder_path:
            return "Android 3.0"
        else:
            return "Android 2.0"
    elif "Server" in folder_path:
        if "BoardMaps 3.0" in folder_path:
            return "Server 3.0"
        else:
            return "Server 2.0"
    else:
        return "Неизвестный тип"


def get_relevant_paths(release_type, folder_paths, server_version=None, ipad_version=None, android_version=None):
    """
    Определяет релевантные пути для загрузки документации на основе типа релиза.
    
    Args:
        release_type (str): Тип релиза (например, 'release2x', 'releaseAndroid2x').
        folder_paths (dict): Словарь путей к папкам на Яндекс.Диске.
        server_version (str, optional): Версия серверной части релиза.
        ipad_version (str, optional): Версия iPad приложения, если она указана.
        android_version (str, optional): Версия Android приложения, если она указана.

    Returns:
        list: Список релевантных путей для загрузки документации.
    """
    relevant_paths = []
    base_release_type = release_type.replace('Android', '').replace('iPad', '')  # Получаем 'release2x' или 'release3x'

    if base_release_type in folder_paths:
        # Если указана версия сервера и тип релиза - сервер
        if server_version and "server" in folder_paths[base_release_type]:
            relevant_paths.extend(folder_paths[base_release_type]["server"])
        
        # Если указана версия iPad и тип релиза - iPad
        if ipad_version and "ipad" in folder_paths[base_release_type]:
            relevant_paths.extend(folder_paths[base_release_type]["ipad"])
        
        # Если указана версия Android и тип релиза - Android
        if android_version and "android" in folder_paths[base_release_type]:
            relevant_paths.extend(folder_paths[base_release_type]["android"])
    else:
        raise KeyError(f"Ключ '{base_release_type}' отсутствует в словаре folder_paths. Проверьте корректность значений.")

    return relevant_paths


def download_and_upload_pdf_files(access_token, nextcloud_url, username, password, folder_paths, release_type, server_version=None, ipad_version=None, android_version=None):
    yandex_manager = YandexDiskManager(access_token)
    nextcloud_manager = NextcloudManager(nextcloud_url, username, password)

    moved_folders = set()  # Для отслеживания уже перемещенных папок
    languages = ["RU", "EN"]

    # Определение релевантных путей для сервера, iPad и Android
    relevant_paths = get_relevant_paths(release_type, folder_paths, server_version, ipad_version, android_version)

    for language in languages:
        # Скачивание и сохранение новых документов в папку
        for folder_path_template in relevant_paths:
            # Подставляем нужную версию в зависимости от платформы
            if 'Android' in folder_path_template:
                version_info = android_version
            elif 'iPad' in folder_path_template or 'iPhone' in folder_path_template:
                version_info = ipad_version
            else:
                version_info = server_version

            # Формируем полный путь, подставляя нужные значения
            folder_path = folder_path_template.format(version_info=version_info, language=language)
            scripts_info_logger.info(f"Используемая версия: {version_info}, Проверка пути: {folder_path}")
            
            items = yandex_manager.get_files_list(folder_path)
            if not items:
                scripts_info_logger.info(f"Элементы не найдены для пути: {folder_path}")
                continue

            product_type = determine_product_type(folder_path)
            if product_type == "Неизвестный тип":
                scripts_error_logger.error(f"Неизвестный тип продукта для папки {folder_path}. Пропуск.")
                continue

            if product_type not in moved_folders:
                src_dir = f"1. Актуальный релиз/Документация/{product_type}"
                dest_dir = f"2. Предыдущие релизы/Документация/{product_type}"
                nextcloud_manager.move_internal_folders(src_dir, dest_dir)
                moved_folders.add(product_type)

            # Формируем путь для папки на Nextcloud
            nextcloud_folder_path = f"1. Актуальный релиз/Документация/{product_type}/{version_info}/{language}"
            scripts_info_logger.info(f"Создание папки на Nextcloud: {nextcloud_folder_path}")
            nextcloud_manager.create_folder(nextcloud_folder_path)

            for item in items:
                item_type = item['type']
                item_name = item['name']

                if item_type == 'file' and (item_name.endswith(".pdf") or item_name.endswith(".txt")):
                    if 'USERS' in folder_path and not item_name.startswith(('U10.0.0', 'U20.0.0')):
                        continue
                    download_url = item['file']
                    local_file_path = os.path.join(tempfile.gettempdir(), item_name)

                    if yandex_manager.download_file(download_url, local_file_path):
                        nextcloud_manager.upload_file(local_file_path, f"{nextcloud_folder_path}/{item_name}")
                        os.remove(local_file_path)



def update_local_documentation(access_token, folder_paths, release_type, language, server_version=None, ipad_version=None, android_version=None):
    """
    Обновляет локальную документацию, скачивая и заменяя файлы в папке 'HTML/attachment'.

    Args:
        access_token (str): Токен доступа Яндекс.Диска.
        folder_paths (dict): Словарь путей к папкам на Яндекс.Диске, содержащим документацию.
        release_type (str): Тип релиза (например, 'release2x' или 'release3x').
        language (str): Язык документации ('RU' или 'EN').
        server_version (str, optional): Версия серверной документации для использования в имени файла.
        ipad_version (str, optional): Версия iPad приложения, если она указана.
        android_version (str, optional): Версия Android приложения, если она указана.
    """
    yandex_manager = YandexDiskManager(access_token)

    # Преобразуем язык в верхний регистр
    language = language.upper()

    attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment', language)

    # Определение релевантных путей для сервера, iPad и Android
    relevant_paths = get_relevant_paths(release_type, folder_paths, server_version, ipad_version, android_version)

    # Скачивание и сохранение новых документов в папку
    for folder_path_template in relevant_paths:
        # Подставляем нужную версию в зависимости от платформы
        if 'Android' in folder_path_template:
            version_info = android_version
        elif 'iPad' in folder_path_template or 'iPhone' in folder_path_template:
            version_info = ipad_version
        else:
            version_info = server_version

        # Формируем полный путь, подставляя нужные значения
        folder_path = folder_path_template.format(version_info=version_info, language=language)
        scripts_info_logger.info(f"Проверка пути: {folder_path}")

        items = yandex_manager.get_files_list(folder_path)
        if items is not None:
            for item in items:
                item_type = item['type']
                item_name = item['name']
                if ('U80.0.0 Список изменений' in item_name or 'Release notes' in item_name) and (
                        f'{server_version}.pdf' in item_name or
                        (ipad_version and f'{ipad_version}.pdf' in item_name) or
                        (android_version and f'{android_version}.pdf' in item_name)):
                    download_url = item['file']
                    local_file_path = os.path.join(attachments_dir, item_name)
                    try:
                        with open(local_file_path, "wb") as file:
                            response = requests.get(download_url, timeout=30)
                            response.raise_for_status()  # Проверяем успешность запроса
                            file.write(response.content)
                        scripts_info_logger.info(f"Скачан новый файл: {item_name}")
                    except (requests.exceptions.RequestException, IOError) as error:
                        scripts_error_logger.error(f"Ошибка при скачивании файла {item_name}: {error}")
        else:
            scripts_error_logger.error(f"Не удалось получить список файлов для пути: {folder_path}")
