import requests
import json
import logging


# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class APIClient:
    def __init__(self, base_url, auth_user, auth_pass):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.auth = (auth_user, auth_pass)
        self.session.headers.update({'Content-Type': 'application/json'})

    def fetch_data(self, endpoint, params=None):
        """Универсальный метод для получения данных с API с поддержкой параметров."""
        url = f'{self.base_url}/{endpoint}'
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            json_response = response.json()
            data = json_response.get('data')
            if data is None:
                logging.error(f'API вернуло ответ без ключа "data" для {endpoint}')
                return None
            return data
        except requests.HTTPError as http_err:
            logging.error(f'HTTP ошибка при запросе к {url}: {http_err}')
        except requests.RequestException as req_err:
            logging.error(f'Ошибка связи при запросе к {url}: {req_err}')
        except ValueError as json_err:
            logging.error(f'Ошибка декодирования JSON при запросе к {url}: {json_err}')
        return None
