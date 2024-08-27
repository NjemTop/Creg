import requests
import base64
import json
from difflib import get_close_matches
import os
from dotenv import load_dotenv


load_dotenv()

TFS_URL = os.environ.get('TFS_URL')
TFS_PASSWORD = os.environ.get('TFS_PASSWORD')
BMS_PROJECT_NAME = os.environ.get('BMS_PROJECT_NAME')


class RequestError(Exception):
    """Класс для обработки ошибок запросов к Azure DevOps."""
    pass

def create_change_request(client_name, assigned_to):
    """
    Создает задачу типа "Change Request" в Azure DevOps для указанного клиента.

    :param client_name: Название клиента, для которого создается задача.
    :type client_name: str
    :param assigned_to: Пользователь, на которого будет назначена задача.
    :type assigned_to: str
    :return: Ответ от сервера Azure DevOps в формате JSON, если запрос выполнен успешно, иначе None.
    :rtype: dict или None

    Функция сначала ищет точное или наиболее близкое совпадение для названия клиента среди списка доступных клиентов.
    Если подходящий клиент найден, функция создает задачу с указанными параметрами.
    При возникновении ошибок выводит соответствующее сообщение.
    """

    # Задаём дефолтные значения для обязательных полей CR
    title = f'Снятие с поддержки клиента {client_name}'
    description = f'Просим снять с поддержки клиента {client_name}'
    module = 'Core'
    platform = 'Server'

    url = f"{TFS_URL}/{BMS_PROJECT_NAME}/_apis/wit/workitems/$Change%20Request?api-version=6.0"
    encoded_pat = str(base64.b64encode(bytes(':' + TFS_PASSWORD, 'utf-8')), 'utf-8')
    headers = {
        'Content-Type': 'application/json-patch+json',
        'Authorization': 'Basic ' + encoded_pat
    }
    data = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": title
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": description
        },
        {
            "op": "add",
            "path": "/fields/bm.Module",
            "value": module
        },
        {
            "op": "add",
            "path": "/fields/bm.Client",
            "value": client_name
        },
        {
            "op": "add",
            "path": "/fields/bm.Platform",
            "value": platform
        },
        {
            "op": "add",
            "path": "/fields/System.AssignedTo",
            "value": assigned_to
        }
    ]
    
    # Логируем данные перед отправкой
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        work_item_url = f"{TFS_URL}/{BMS_PROJECT_NAME}/_workitems/edit/{result['id']}/"
        return {
            'id': result['id'],
            'type': result['fields']['System.WorkItemType'],
            'assigned_to': result['fields']['System.AssignedTo']['displayName'],
            'url': work_item_url
        }
    except requests.RequestException as error_message:
        raise RequestError(f"Ошибка создания 'Change Request': {str(error_message)}")


if __name__ == "__main__":
    try:
        info = create_change_request("Уралкалий", "Sergey Fedorov")
        print(info)
    except RequestError as e:
        print(e)
