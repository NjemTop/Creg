from atlassian import Confluence
from bs4 import BeautifulSoup
import json
import logging
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

# Настройки логирование для атлассиан клиента и HTTP клиента
logging.getLogger("atlassian").setLevel(logging.WARNING)
logging.getLogger("rest_client").setLevel(logging.WARNING)

def get_server_release_notes(server_version):
    """
    Получает информацию о релизе сервера с Confluence.

    Args:
        server_version (str): Версия сервера.

    Returns:
        dict: Словарь с обновлениями сервера на русском и английском языках.
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
            server_updates = extract_content(server_page_content)
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
        dict: Словарь с обновлениями iPad на русском и английском языках.
    """
    if not ipad_version:
        scripts_info_logger.info("Мобильная версия iPad не указана.")
        return {'Русский': [], 'Английский': []}

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
        confluence = Confluence(url=url, username=USERNAME, password=PASSWORD)
    except Exception as error_message:
        error_message = (f"Не удалось создать объект Confluence: {str(error_message)}")
        scripts_error_logger.error(error_message)
        raise Exception(error_message)

    ipad_title = f"BM iOS/iPadOS {ipad_version}"

    try:
        ipad_page_content = confluence.get_page_by_title(title=ipad_title, space="development", expand='body.view')
        if not ipad_page_content or 'results' in ipad_page_content and not ipad_page_content['results']:
            scripts_error_logger.error(f"Страница {ipad_title} не найдена.")
            return {'Русский': [], 'Английский': []}  # Возвращаем пустой словарь, если страница не найдена
        ipad_updates = extract_content(ipad_page_content)
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
        dict: Словарь с обновлениями Android на русском и английском языках.
    """
    if not android_version:
        scripts_info_logger.info("Мобильная версия Android не указана.")
        return {'Русский': [], 'Английский': []}

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
        confluence = Confluence(url=url, username=USERNAME, password=PASSWORD)
    except Exception as error_message:
        error_message = (f"Не удалось создать объект Confluence: {str(error_message)}")
        scripts_error_logger.error(error_message)
        raise Exception(error_message)

    android_title = f"Android {android_version}"

    try:
        android_page_content = confluence.get_page_by_title(title=android_title, space="development", expand='body.view')
        if android_page_content:
            android_updates = extract_content(android_page_content)
        else:
            scripts_error_logger.error(f"Страница {android_title} не найдена.")
    except Exception as error_message:
        scripts_error_logger.error(f"Не удалось получить страницы: {str(error_message)}")
        raise Exception(error_message)

    return android_updates


def extract_content(page_content):
    """
    Извлекает контент страницы, проверяя наличие таблиц после заголовка.

    Args:
        page_content (dict): Контент страницы, полученный из Confluence.

    Returns:
        dict: Словарь с обновлениями на русском и английском языках.
    """
    # Создаем объект BeautifulSoup из HTML тела страницы
    soup = BeautifulSoup(page_content['body']['view']['value'], 'html.parser')

    # Проверяем наличие таблиц после заголовка
    header = soup.find('h1', text='Текст для оповещения о новой версии')
    if header:
        tables = header.find_all_next('table')
        if tables:
            return extract_tables(tables)

    # Если таблиц нет, используем старый метод
    return extract_list(page_content)


def extract_tables(tables):
    """
    Извлекает обновления из таблиц на странице.

    Args:
        tables (ResultSet): Список таблиц, найденных на странице.

    Returns:
        dict: Словарь с обновлениями на русском и английском языках.
    """
    # Инициализируем словарь для обновлений
    updates = {'Русский': [], 'Английский': []}

    # Обрабатываем таблицу
    for table in tables:
        rows = table.find_all('tr')
        current_language = None

        for row in rows:
            th = row.find('th')
            if th:
                current_language = th.get_text(strip=True)
                if current_language not in updates:
                    current_language = None  # Reset if language is not recognized
                continue

            td = row.find('td')
            if td and current_language:
                list_items = td.find_all('li')
                for item in list_items:
                    text = item.get_text(strip=True)
                    updates[current_language].append(text)

    # Проверка наличия текста на русском и английском языках
    if not updates['Русский']:
        warning_message = "Текст на русском языке отсутствует."
        scripts_info_logger.warning(warning_message)

    if not updates['Английский']:
        warning_message = "Текст на английском языке отсутствует."
        scripts_info_logger.warning(warning_message)

    return updates


def extract_list(page_content):
    """
    Извлекает обновления из списка на странице.

    Args:
        page_content (dict): Контент страницы, полученный из Confluence.

    Returns:
        dict: Словарь с обновлениями на русском языке.
    """
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
        return {'Русский': updates, 'Английский': []}  # Возвращаем старый тип рассылки с только русским языком
    else:
        error_message = "Не найден список после заголовка."
        scripts_error_logger.error(error_message)
        raise Exception(error_message)
