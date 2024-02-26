import json
import requests
import base64
import logging
from logger.log_config import setup_logger, get_abs_log_path
import os
from dotenv import load_dotenv


load_dotenv()


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


TFS_USER = os.environ.get('TFS_USER')
TFS_PASSWORD = os.environ.get('TFS_PASSWORD')
TFS_URL = os.environ.get('TFS_URL')

def trigger_tfs_pipeline(client_name):
    url = f'{TFS_URL}/346bbe88-c194-4b45-a6e1-7df74c908c3a/_apis/pipelines/148/runs?api-version=6.0-preview.1'

    base64string = base64.b64encode(f"{TFS_USER}:{TFS_PASSWORD}".encode('utf-8')).decode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {base64string}'
    }

    data = {
        "resources": {
            "repositories": {
                "self": {
                    "refName": "master"
                }
            }
        },
        "variables": {
            "new_client": {
                "isSecret": False,
                "value": client_name
            },
            "add_client": {
                "isSecret": False,
                "value": True
            }
        }
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        scripts_error_logger.info(f'Pipeline успешно запущен для клиента: {client_name}')
    else:
        scripts_error_logger.error(f"Не удалось запустить pipeline для клиента: {client_name}. Ошибка: {response.text}")
