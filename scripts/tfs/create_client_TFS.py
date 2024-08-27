import json
import requests
import base64
import os
from dotenv import load_dotenv
import logging
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
scripts_error_logger = setup_logger('scripts_error', get_abs_log_path('scripts_errors.log'), logging.ERROR)
scripts_info_logger = setup_logger('scripts_info', get_abs_log_path('scripts_info.log'), logging.INFO)


load_dotenv()

TFS_URL = os.environ.get('TFS_URL')
TFS_PASSWORD = os.environ.get('TFS_PASSWORD')
DEVOPS_PROJECT_ID = os.environ.get('DEVOPS_PROJECT_ID')
PIPELINE_ID = os.environ.get('PIPELINE_ID')


def trigger_tfs_pipeline(client_name):
    url = f'{TFS_URL}/{DEVOPS_PROJECT_ID}/_apis/pipelines/{PIPELINE_ID}/runs?api-version=6.0-preview.1'

    encoded_pat = str(base64.b64encode(bytes(':' + TFS_PASSWORD, 'utf-8')), 'utf-8')
    headers = {
        'Authorization': 'Basic ' + encoded_pat
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
        run_id = response.json()['id']  # Получаем run_id из ответа
        return run_id
    else:
        scripts_error_logger.error(f"Не удалось запустить pipeline для клиента: {client_name}. Ошибка: {response.text}")
        return None

if __name__ == "__main__":
    trigger_tfs_pipeline("Тестовый клиент")
