import requests
import json
import logging
from logger.log_config import setup_logger, get_abs_log_path
import os
from django.conf import settings
from dotenv import load_dotenv


load_dotenv()

# Указываем настройки логов для нашего файла
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)

# Указываем путь к файлу с данными
CONFIG_FILE = os.path.join(settings.BASE_DIR, "Main.config")

if os.getenv('GITHUB_ACTIONS') == 'true':
    # Заглушка для данных конфигурации
    DATA = {
        'TELEGRAM_SETTINGS': {
            'BOT_TOKEN': 'mocked_bot_token'
        }
    }
else:
    # Читаем данные из файла
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
        DATA = json.load(file)

# Получаем значение ключа BOT_TOKEN в TELEGRAM_SETTINGS
BOT_TOKEN = DATA['TELEGRAM_SETTINGS']['BOT_TOKEN']

class Alert():
    # ФУНКЦИЯ ОТПРАВКИ АЛЕРТА В ЧАТ
    def send_telegram_message(self, alert_chat_id, alert_text):
        """
        Отправляет сообщение в телеграм-бот.
        На себя принимает два аргумента:
        alert_chat_id - чат айди, куда мы будем отправлять сообщение,
        alert_text - текст сообщения, которое мы хотим отправить.
        """
        # Адрес для отправки сообщения напрямую через API Telegram
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        # Задаём стандартный заголовок отправки
        headers_server = {'Content-type': 'application/json'}
        # Создаём тело запроса, которое мы отправляем
        data = {
            'chat_id': alert_chat_id,
            'text': f'{alert_text}',
            'parse_mode': 'HTML'
        }
        # Отправляем запрос через наш бот
        response = requests.post(url, headers=headers_server, data=json.dumps(data), timeout=30)
        # Добавляем логгирование для отладки
        scripts_info_logger.info(f"Сообщение контакту '{alert_chat_id}' было отправлено. Ответ: {response}")
