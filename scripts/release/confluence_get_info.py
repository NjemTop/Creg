from atlassian import Confluence
from bs4 import BeautifulSoup
import json
import logging
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts', get_abs_log_path('scripts_info.log'), logging.INFO)


def get_server_release_notes(server_version):
    """
    Получает информацию о релизе сервера с Confluence.
    
    Args:
        server_version (str): Версия сервера.
    
    Returns:
        list: Список обновлений сервера.
    """
    server_updates = None

    # Указываем путь к файлу с данными
    CONFIG_FILE = "Main.config"
    # Открываем файл и загружаем данные
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
        data = json.load(file)

    # Получаем учётные данные из конфиг-файла для доступа к Confluence
    USERNAME = data["FILE_SHARE"]["USERNAME"]
    PASSWORD = data["FILE_SHARE"]["PASSWORD"]

    # Адрес Confluence
    url = 'https://confluence.boardmaps.ru'

    try:
        # Создаем объект Confluence
        confluence = Confluence(
            url=url,
            username=USERNAME,
            password=PASSWORD)
    except Exception as error_message:
        error_message = (f"Не удалось создать объект Confluence: {str(error_message)}")
        scripts_error_logger.error(error_message)
        raise Exception(error_message)

    server_title = f"BM {server_version}"
    try:
        server_page_content = confluence.get_page_by_title(title=server_title, space="development", expand='body.view')
        if server_page_content:
            server_updates = extract_list(server_page_content)
    except Exception as error_message:
        scripts_error_logger.error(f"Не удалось получить страницы: {str(error_message)}")
        raise Exception(error_message)

    return server_updates


def get_ipad_release_notes(ipad_version):
    """
    Получает информацию о релизе iPad с Confluence.
    
    Args:
        ipad_version (str): Версия iPad.
    
    Returns:
        list: Список обновлений iPad.
    """
    ipad_updates = None

    # Указываем путь к файлу с данными
    CONFIG_FILE = "Main.config"
    # Открываем файл и загружаем данные
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
        data = json.load(file)

    # Получаем учётные данные из конфиг-файла для доступа к Confluence
    USERNAME = data["FILE_SHARE"]["USERNAME"]
    PASSWORD = data["FILE_SHARE"]["PASSWORD"]

    # Адрес Confluence
    url = 'https://confluence.boardmaps.ru'

    try:
        # Создаем объект Confluence
        confluence = Confluence(
            url=url,
            username=USERNAME,
            password=PASSWORD)
    except Exception as error_message:
        error_message = (f"Не удалось создать объект Confluence: {str(error_message)}")
        scripts_error_logger.error(error_message)
        raise Exception(error_message)

    ipad_title = f"BM iOS/iPadOS {ipad_version}"

    try:
        ipad_page_content = confluence.get_page_by_title(title=ipad_title, space="development", expand='body.view')
        if ipad_page_content:
            ipad_updates = extract_list(ipad_page_content)
    except Exception as error_message:
        scripts_error_logger.error(f"Не удалось получить страницы: {str(error_message)}")
        raise Exception(error_message)

    return ipad_updates


def get_android_release_notes(android_version):
    """
    Получает информацию о релизе Android с Confluence.
    
    Args:
        android_version (str): Версия Android.
    
    Returns:
        list: Список обновлений Android.
    """
    android_updates = None

    # Указываем путь к файлу с данными
    CONFIG_FILE = "Main.config"
    # Открываем файл и загружаем данные
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
        data = json.load(file)

    # Получаем учётные данные из конфиг-файла для доступа к Confluence
    USERNAME = data["FILE_SHARE"]["USERNAME"]
    PASSWORD = data["FILE_SHARE"]["PASSWORD"]

    # Адрес Confluence
    url = 'https://confluence.boardmaps.ru'

    try:
        # Создаем объект Confluence
        confluence = Confluence(
            url=url,
            username=USERNAME,
            password=PASSWORD)
    except Exception as error_message:
        error_message = (f"Не удалось создать объект Confluence: {str(error_message)}")
        scripts_error_logger.error(error_message)
        raise Exception(error_message)

    android_title = f"Android {android_version}"

    try:
        android_page_content = confluence.get_page_by_title(title=android_title, space="development", expand='body.view')
        if android_page_content:
            android_updates = extract_list(android_page_content)
    except Exception as error_message:
        scripts_error_logger.error(f"Не удалось получить страницы: {str(error_message)}")
        raise Exception(error_message)

    return android_updates


def extract_list(page_content):
    # Создаем объект BeautifulSoup из HTML тела страницы
    soup = BeautifulSoup(page_content['body']['view']['value'], 'html.parser')

    # Находим заголовок "Текст для оповещения о новой версии"
    header = soup.find('h1', text='Текст для оповещения о новой версии')

    # Находим ближайший список <ol> или <ul> после заголовка
    list = header.find_next_sibling(['ol', 'ul'])

    # Если список найден
    if list is not None:
        updates = []
        for item in list.find_all('li'):
            text = item.text.strip()
            # Проверяем, содержит ли элемент подпункты
            if item.find(['ol', 'ul']):
                # Извлекаем только основной текст элемента, исключая подпункты
                text = ''.join(item.find_all(text=True, recursive=False)).strip()
            updates.append(text)
        return updates
    else:
        error_message = "Не найден список после заголовка."
        scripts_error_logger.error(error_message)
        raise Exception(error_message)
