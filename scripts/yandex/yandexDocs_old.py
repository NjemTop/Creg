import requests
from urllib.parse import quote
import os
import traceback
import tempfile
import time
import logging
from logger.log_config import setup_logger, get_abs_log_path
import requests.exceptions
from django.conf import settings
from scripts.nextcloud.move_file import NextcloudMover


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

# Константы
MAX_RETRIES = 5
RETRY_DELAY = 5  # Задержка между попытками (в секундах)
REQUEST_TIMEOUT = 30  # Тайм-аут для HTTP-запросов

def determine_product_type(folder_path):
    """
    Определяет тип продукта на основе пути к папке.

    Args:
        folder_path (str): Путь к папке на Яндекс.Диске.

    Returns:
        str: Название промежуточной папки на основе типа продукта.
    """
    if "iPad" in folder_path or "iPhone" in folder_path:
        return "iOS_iPadOS 2.0"
    elif "Android" in folder_path:
        return "Android"
    elif "Server" in folder_path and "BoardMaps 3.0" not in folder_path:
        return "Server 2.0"
    elif "BoardMaps 3.0" in folder_path:
        return "Server 3.0"
    # Условие для будущего iPad 3.0 "iOS_iPadOS 3.0"
    # elif "<Название папки>" in folder_path:
    #     return "iOS_iPadOS 3.0"
    else:
        return "Неизвестный тип"

def download_and_upload_pdf_files(access_token, nextcloud_url, username, password, version, folder_paths, release_type, ipad_version=None, android_version=None):
    """
    Функция для скачивания PDF-файлов с Яндекс.Диска и загрузки их на Nextcloud.

    Args:
        access_token (str): Токен доступа Яндекс.Диска.
        nextcloud_url (str): URL-адрес Nextcloud.
        username (str): Имя пользователя Nextcloud.
        password (str): Пароль пользователя Nextcloud.
        version (str): Версия документации для использования в имени папки.
        folder_paths (dict): Словарь путей к папкам на Яндекс.Диске, которые нужно обработать.
        release_type (str): Тип релиза (например, 'release2x' или 'release3x').
        ipad_version (str, optional): Версия iPad приложения.
        android_version (str, optional): Версия Android приложения.

    """
    # Создание экземпляра класса NextcloudMover
    nextcloud_mover = NextcloudMover(nextcloud_url, username, password)
    moved_folders = set()  # Для отслеживания уже перемещенных папок

    languages = ["RU", "EN"]
    try:
        relevant_paths = []

        # Проверяем пути для основного релиза
        if release_type in folder_paths:
            relevant_paths.extend(folder_paths[release_type])
        
        # Проверяем пути для мобильных версий, если указаны
        if ipad_version and 'ipad' in folder_paths:
            relevant_paths.extend(folder_paths['ipad'])
        
        if android_version and 'android' in folder_paths:
            relevant_paths.extend(folder_paths['android'])

        for language in languages:
            # Проходимся циклом по всем папкам с Яндекс.Диска
            for folder_path_template in relevant_paths:
                folder_path = folder_path_template.format(version_info=version if "Server" in folder_path_template else ipad_version if "iPad" in folder_path_template else android_version, language=language)
                scripts_info_logger.info(f"Проверка пути: {folder_path}")
                
                # Повторные попытки при ошибках
                items = None
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        items = get_yandex_disk_files_list(access_token, folder_path)
                        if items:
                            break
                    except Exception as e:
                        scripts_error_logger.error(f"Попытка {attempt}/{MAX_RETRIES} не удалась для пути {folder_path}: {str(e)}")
                        if attempt == MAX_RETRIES:
                            raise
                        time.sleep(RETRY_DELAY)

                if not items:  # Если список элементов пуст, пропускаем перемещение для этого пути
                    scripts_info_logger.info(f"Элементы не найдены для пути: {folder_path}")
                    continue

                product_type = determine_product_type(folder_path)  # Определение типа продукта
                if product_type == "Неизвестный тип":
                    scripts_error_logger.error(f"Неизвестный тип продукта для папки {folder_path}. Пропуск.")
                    continue

                # Перемещаем старые файлы только если для данного product_type это еще не сделано
                if product_type not in moved_folders:
                    src_dir = f"1. Актуальный релиз/Документация/{product_type}"
                    dest_dir = f"2. Предыдущие релизы/Документация/{product_type}"
                    nextcloud_mover.move_internal_folders(src_dir, dest_dir)
                    moved_folders.add(product_type)  # Помечаем product_type как обработанный

                # Создание папки для новой версии документации и загрузка файлов
                nextcloud_folder_path = f"1. Актуальный релиз/Документация/{product_type}/{version if 'Server' in folder_path_template else ipad_version if 'iPad' in folder_path_template else android_version}/{language}"
                create_nextcloud_folder(nextcloud_folder_path, nextcloud_url, username, password)

                for item in items:
                    item_type = item['type']
                    item_name = item['name']

                    # Загрузка файла с Яндекс.Диска
                    if item_type == 'file' and (item_name.endswith(".pdf") or item_name.endswith(".txt")):
                        if 'USERS' in folder_path and not item_name.startswith(('U10.0.0', 'U20.0.0')):
                            continue
                        download_url = item['file']
                        local_file_path = os.path.join(tempfile.gettempdir(), item_name)
                        for attempt in range(1, MAX_RETRIES + 1):
                            try:
                                with open(local_file_path, "wb") as file:
                                    response = requests.get(download_url, timeout=REQUEST_TIMEOUT)
                                    response.raise_for_status()  # Проверяем успешность запроса
                                    file.write(response.content)

                                remote_file_path = f"{nextcloud_folder_path}/{item_name}"
                                upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, username, password)
                                os.remove(local_file_path)
                                break
                            except (requests.exceptions.RequestException, IOError) as e:
                                scripts_error_logger.error(f"Попытка {attempt}/{MAX_RETRIES} не удалась для файла {item_name}: {str(e)}")
                                if attempt == MAX_RETRIES:
                                    raise
                                time.sleep(RETRY_DELAY)

                # Задержка между загрузками документов
                time.sleep(RETRY_DELAY)

    except Exception as error:
        error_msg = f"Необработанное исключение функции скачивания и загрузки файлов: {error}"
        error_traceback = traceback.format_exc()  # Получаем полный стек вызовов в виде строки
        scripts_error_logger.error(f"{error_msg}\nПолный стек вызовов: {error_traceback}")
        raise

def create_nextcloud_folder(folder_path, nextcloud_url, username, password):
    """
    Функция для создания папки на Nextcloud с рекурсивным созданием всех родительских папок.

    Args:
        folder_path (str): Путь к папке, которую нужно создать на Nextcloud.
        nextcloud_url (str): URL-адрес сервера Nextcloud.
        username (str): Имя пользователя для аутентификации на сервере Nextcloud.
        password (str): Пароль для аутентификации на сервере Nextcloud.

    """
    try:
        parts = folder_path.strip('/').split('/')
        for i in range(1, len(parts) + 1):
            sub_folder_path = '/'.join(parts[:i])
            url = f"{nextcloud_url}/remote.php/dav/files/{username}/{sub_folder_path}"
            response = requests.request("MKCOL", url, auth=(username, password), timeout=REQUEST_TIMEOUT)
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

def upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, username, password):
    """
    Функция для загрузки файлов на Nextcloud.

    Args:
        local_file_path (str): Путь к локальному файлу, который нужно загрузить на Nextcloud.
        remote_file_path (str): Путь к файлу на сервере Nextcloud, куда файл будет загружен.
        nextcloud_url (str): URL-адрес сервера Nextcloud.
        username (str): Имя пользователя для аутентификации на сервере Nextcloud.
        password (str): Пароль для аутентификации на сервере Nextcloud.

    """
    url = f"{nextcloud_url}/remote.php/dav/files/{username}/{remote_file_path}"
    with open(local_file_path, "rb") as file:
        response = requests.put(url, data=file, auth=(username, password), timeout=REQUEST_TIMEOUT)
    if response.status_code == 201:
        scripts_info_logger.info("Файл %s успешно загружен на Nextcloud.", local_file_path)
    else:
        scripts_error_logger.error("Ошибка при загрузке файла %s на Nextcloud. Код статуса: %s, Текст ошибки: %s", local_file_path, response.status_code, response.text)

def get_yandex_disk_files_list(access_token, folder_path):
    """
    Функция для получения списка файлов и папок, находящихся на Яндекс.Диске в указанной папке.

    Args:
        access_token (str): Токен доступа Яндекс.Диска.
        folder_path (str): Путь к папке на Яндекс.Диске, для которой нужно получить список файлов.

    Returns:
        list: Список элементов (файлов и папок) в указанной папке на Яндекс.Диске. 
              В случае ошибки возвращает пустой список.
    """
    headers = {
        "Authorization": f"OAuth {access_token}"
    }
    encoded_folder_path = quote(folder_path)
    url = f"https://cloud-api.yandex.net/v1/disk/resources?path={encoded_folder_path}&limit=100"
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as error:
        scripts_error_logger.error("Ошибка при выполнении запроса: %s", error)
        return []  # Возвращаем пустой список
    
    if response.status_code == 200:
        response_data = response.json()
        items = response_data['_embedded']['items']
        return items
    else:
        scripts_error_logger.error("Ошибка при получении списка файлов. Код статуса: %s, Текст ошибки: %s", response.status_code, response.text)
        return []  # Возвращаем пустой список

def update_local_documentation(access_token, server_version, folder_paths, release_type, language, ipad_version=None, android_version=None):
    """
    Обновляет локальную документацию, скачивая и заменяя файлы в папке 'HTML/attachment'.

    Args:
        access_token (str): Токен доступа Яндекс.Диска.
        server_version (str): Версия серверной документации для использования в имени файла.
        folder_paths (dict): Словарь путей к папкам на Яндекс.Диске, содержащим документацию.
        release_type (str): Тип релиза (например, 'release2x' или 'release3x').
        language (str): Язык документации ('RU' или 'EN').
        ipad_version (str, optional): Версия iPad приложения, если она указана.
        android_version (str, optional): Версия Android приложения, если она указана.
    """
    attachments_dir = os.path.join(settings.BASE_DIR, 'scripts', 'release', 'HTML', 'attachment')

    # Преобразуем язык в верхний регистр
    language = language.upper()

    try:
        # Удаление старых документов из папки
        for attachment in os.listdir(attachments_dir):
            os.remove(os.path.join(attachments_dir, attachment))
            scripts_info_logger.info("Удален старый файл: %s", attachment)

        # Определение путей для загрузки в зависимости от релиза и наличия мобильной версии
        relevant_paths = []

        if release_type in folder_paths:
            relevant_paths.extend([path.format(version_info=server_version, language=language) for path in folder_paths[release_type]])
        
        if ipad_version and 'ipad' in folder_paths:
            for path in folder_paths['ipad']:
                relevant_paths.append(path.format(version_info=ipad_version, language=language))
        
        if android_version and 'android' in folder_paths:
            for path in folder_paths['android']:
                relevant_paths.append(path.format(version_info=android_version, language=language))
        
        # Логирование путей для отладки
        scripts_info_logger.info("Форматированные пути для загрузки документации: %s", relevant_paths)

        # Скачивание и сохранение новых документов в папку
        for folder_path in relevant_paths:
            folder_path = folder_path.format(version_info=server_version)
            items = get_yandex_disk_files_list(access_token, folder_path)
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
                            scripts_info_logger.info("Скачан новый файл: %s", item_name)
                        except (requests.exceptions.RequestException, IOError) as error:
                            scripts_error_logger.error("Ошибка при скачивании файла %s: %s", item_name, error)
            else:
                scripts_error_logger.error("Не удалось получить список файлов для пути: %s", folder_path)
    except Exception as error:
        scripts_error_logger.error("Произошла общая ошибка: %s", error)
