from atlassian import Confluence
from bs4 import BeautifulSoup
import json
import os
import logging
from apps.mailings.services.utils.config import get_config_path
from apps.configurations.config_loader import get_integration_settings

logger = logging.getLogger(__name__)

logging.getLogger("atlassian").setLevel(logging.WARNING)
logging.getLogger("rest_client").setLevel(logging.WARNING)


def get_server_release_notes(server_version, lang_key):
    server_updates = None
    data = get_integration_settings()
    USERNAME = data.get("CONFLUENCE", {}).get("USERNAME")
    PASSWORD = data.get("CONFLUENCE", {}).get("PASSWORD")
    url = 'https://confluence.boardmaps.ru'
    try:
        confluence = Confluence(url=url, username=USERNAME, password=PASSWORD)
    except Exception as error_message:
        logger.error("Не удалось создать объект Confluence: %s", error_message)
        raise
    server_title = f"BM {server_version}"
    try:
        page = confluence.get_page_by_title(title=server_title, space="development", expand='body.view')
        if page:
            server_updates = extract_content(page)
            return server_updates.get(lang_key, [])
    except Exception as error_message:
        logger.error("Не удалось получить страницы: %s", error_message)
        raise
    return []


def get_ipad_release_notes(ipad_version, lang_key):
    if not ipad_version:
        logger.info("Мобильная версия iPad не указана.")
        return []
    data = get_integration_settings()
    USERNAME = data.get("CONFLUENCE", {}).get("USERNAME")
    PASSWORD = data.get("CONFLUENCE", {}).get("PASSWORD")
    url = 'https://confluence.boardmaps.ru'
    try:
        confluence = Confluence(url=url, username=USERNAME, password=PASSWORD)
    except Exception as error_message:
        logger.error("Не удалось создать объект Confluence: %s", error_message)
        raise
    ipad_title = f"BM iOS/iPadOS {ipad_version}"
    try:
        page = confluence.get_page_by_title(title=ipad_title, space="development", expand='body.view')
        if not page or ('results' in page and not page['results']):
            logger.error("Страница %s не найдена.", ipad_title)
            return []
        ipad_updates = extract_content(page)
        return ipad_updates.get(lang_key, [])
    except Exception as error_message:
        logger.error("Не удалось получить страницы: %s", error_message)
        raise


def get_android_release_notes(android_version, lang_key):
    if not android_version:
        logger.info("Мобильная версия Android не указана.")
        return []
    data = get_integration_settings()
    USERNAME = data.get("CONFLUENCE", {}).get("USERNAME")
    PASSWORD = data.get("CONFLUENCE", {}).get("PASSWORD")
    url = 'https://confluence.boardmaps.ru'
    try:
        confluence = Confluence(url=url, username=USERNAME, password=PASSWORD)
    except Exception as error_message:
        logger.error("Не удалось создать объект Confluence: %s", error_message)
        raise
    android_title = f"Android {android_version}"
    try:
        page = confluence.get_page_by_title(title=android_title, space="development", expand='body.view')
        if page:
            android_updates = extract_content(page)
            return android_updates.get(lang_key, [])
        else:
            logger.error("Страница %s не найдена.", android_title)
            return []
    except Exception as error_message:
        logger.error("Не удалось получить страницы: %s", error_message)
        raise


def extract_content(page_content):
    soup = BeautifulSoup(page_content['body']['view']['value'], 'html.parser')
    header = soup.find('h1', text='Текст для оповещения о новой версии')
    if header:
        tables = header.find_all_next('table')
        if tables:
            return extract_tables(tables)
    return extract_list(page_content)


def extract_tables(tables):
    updates = {'Русский': [], 'Английский': []}
    for table in tables:
        rows = table.find_all('tr')
        current_language = None
        for row in rows:
            h4 = row.find('h4')
            if h4:
                current_language = h4.get_text(strip=True)
                if current_language not in updates:
                    current_language = None
                continue
            td = row.find('td')
            if td and current_language:
                list_items = td.find('ol') or td.find('ul')
                if list_items:
                    for item in list_items.find_all('li'):
                        text = item.get_text(strip=True)
                        updates[current_language].append(text)
                else:
                    text = td.get_text(strip=True)
                    if text:
                        updates[current_language].append(text)
    if not updates['Русский']:
        logger.warning("Текст на русском языке отсутствует.")
    if not updates['Английский']:
        logger.warning("Текст на английском языке отсутствует.")
    return updates


def extract_list(page_content):
    soup = BeautifulSoup(page_content['body']['view']['value'], 'html.parser')
    header = soup.find(['h1', 'h2'], text=lambda t: t and 'текст для оповещения о новой версии' in t.lower())
    if not header:
        all_headers = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])]
        error_message = (
            "Заголовок 'Текст для оповещения о новой версии' не найден. "
            "Проверьте структуру статьи в Confluence.\n"
            f"Найденные заголовки на странице: {all_headers}"
        )
        save_debug_html(soup)
        logger.error(error_message)
        raise Exception(error_message)
    list_element = header.find_next_sibling(['ol', 'ul'])
    if not list_element:
        error_message = (
            "Список обновлений после заголовка 'Текст для оповещения о новой версии' не найден. "
            "Убедитесь, что структура статьи корректна."
        )
        save_debug_html(soup)
        logger.error(error_message)
        raise Exception(error_message)
    updates = []
    for item in list_element.find_all('li'):
        text = item.text.strip()
        if item.find(['ol', 'ul']):
            text = ''.join(item.find_all(text=True, recursive=False)).strip()
        updates.append(text)
    return {'Русский': updates, 'Английский': []}


def save_debug_html(soup):
    logs_dir = "/app/logs"
    os.makedirs(logs_dir, exist_ok=True)
    debug_file_path = os.path.join(logs_dir, "debug_page_content.html")
    try:
        with open(debug_file_path, 'w', encoding='utf-8') as debug_file:
            debug_file.write(soup.prettify())
        logger.info("HTML страницы сохранен в %s для отладки.", debug_file_path)
    except Exception as e:
        logger.error("Не удалось сохранить HTML для отладки: %s", e)
