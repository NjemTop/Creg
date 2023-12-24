import re
import json
import socket
from urllib.parse import urlparse
from pypsrp.client import Client


def normalize_hostname(url):
    """
    Нормализует введенный хостнейм, удаляя схему и путь, если они присутствуют.
    :param url: URL или хостнейм для нормализации.
    :return: Нормализованный хостнейм.
    """
    # Добавляем протокол, если он отсутствует, для удобства парсинга
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    # Извлекаем и возвращаем часть хоста из URL
    parsed_url = urlparse(url)
    return parsed_url.hostname


def get_mssql_info(hostname, username, password):
    """
    Получает информацию о сайте IIS и строку подключения к базе данных из файла конфигурации.
    :param hostname: Хостнейм сайта.
    :param username: Имя пользователя для аутентификации.
    :param password: Пароль пользователя.
    :return: Словарь с информацией о базе данных или None в случае ошибки.
    """
    try:
        # Приводим хостнейм к стандартному виду
        hostname = normalize_hostname(hostname)
        # Получаем IP адрес из доменного имени
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        print("Ошибка: Невозможно получить IP адрес для данного хостнейма.")
        return None

    # Создаем клиент WinRM для подключения к серверу
    client = Client(
        ip_address,
        username=username,
        password=password,
        ssl=False,
        auth="negotiate"
    )

    # Выполнение PowerShell скрипта для получения информации о сайтах IIS
    ps_script = """
    Import-Module WebAdministration
    $websites = Get-Website | Select-Object Name,State,PhysicalPath,@{Name='Bindings';Expression={$_.bindings.Collection -join ' '}} | ConvertTo-Json
    $websites
    """

    # Выполнение скрипта и обработка возможных ошибок
    output, streams, had_errors = client.execute_ps(ps_script)
    if had_errors:
        print("Ошибка при выполнении скрипта PowerShell:", streams.error)
        return None

    # Преобразование результата из JSON
    websites = json.loads(output)
    if isinstance(websites, dict):  # Если результат — одиночный объект, оборачиваем его в список
        websites = [websites]

    # Поиск информации о сайте по hostname
    site_info = next((site for site in websites if hostname in site['Bindings']), None)
    if not site_info:
        print(f"Сайт с hostname {hostname} не найден.")
        return None

    # Путь к файлу конфигурации строк подключения
    site_path = site_info['physicalPath']
    config_file_path = f"{site_path}\\ConnectionStrings.config"

    # Получение содержимого файла конфигурации
    get_config_script = f"Get-Content -Path '{config_file_path}' -Raw"
    config_output, config_streams, config_had_errors = client.execute_ps(get_config_script)
    if config_had_errors:
        print("Ошибка при получении файла конфигурации:", config_streams.error)
        return None

    # Регулярное выражение для извлечения данных из строки подключения
    db_data_pattern = r'connectionString="Data Source=(?P<server>[^;]+);Initial Catalog=(?P<database>[^;]+);.*User ID=(?P<user>[^;]+);Password=(?P<password>[^"]+)"'
    db_data_match = re.search(db_data_pattern, config_output)
    if db_data_match:
        # Извлекаем только имя сервера, не включая доменное имя
        db_server_full = db_data_match.group('server')
        # Разделяем по точке и берем первый элемент
        db_server_name_only = db_server_full.split('.')[0]

        # Возвращаем информацию в виде словаря
        return {
            'db_server': db_server_name_only,
            'db_name': db_data_match.group('database'),
            'db_user': db_data_match.group('user'),
            'db_password': db_data_match.group('password')
        }
    else:
        print("'Connection string' не найдена или файл конфигурации имеет неверный формат.")
        return None


# hostname_input = "https://demo-impl4.boardmaps.ru/"
# username = "corp\oeliseev"
# password = "Rfnzkj0604"

# db_info = get_mssql_info(hostname_input, username, password)
# if db_info:
#     print(f"DB Server: {db_info['db_server']}")
#     print(f"DB Name: {db_info['db_name']}")
#     print(f"DB User: {db_info['db_user']}")
#     print(f"DB Password: {db_info['db_password']}")
