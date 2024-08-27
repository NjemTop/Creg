import requests
import base64
import json
import os
from dotenv import load_dotenv


load_dotenv()

TFS_URL = os.environ.get('TFS_URL')
TFS_PASSWORD = os.environ.get('TFS_PASSWORD')
BMS_PROJECT_NAME = os.environ.get('BMS_PROJECT_NAME')
FOLDER_ID_CLIENTS = os.environ.get('FOLDER_ID_CLIENTS')


def get_clients_dict(folder_id):
    """
    Получает список клиентов из папки запросов в Azure DevOps и возвращает словарь с клиентами.

    :param folder_id: Идентификатор папки запросов в Azure DevOps.
    :type folder_id: str
    :return: Словарь, где ключи — это названия клиентов в нижнем регистре, а значения — их идентификаторы.
    :rtype: dict или None

    Функция делает HTTP-запрос к Azure DevOps для получения данных о запросах.
    В случае успешного запроса, парсит полученный JSON и строит словарь клиентов.
    В случае ошибки запроса или обработки данных возвращает None и выводит ошибку в консоль.
    """
    encoded_pat = str(base64.b64encode(bytes(':' + TFS_PASSWORD, 'utf-8')), 'utf-8')
    headers = {
        'Authorization': 'Basic ' + encoded_pat
    }
    queries_url = f"{TFS_URL}/{BMS_PROJECT_NAME}/_apis/wit/queries/{folder_id}?api-version=6.0&$depth=1"

    clients_dict = {}

    try:
        response = requests.get(queries_url, headers=headers)
        response.raise_for_status()
        queries_in_folder = response.json().get('children', [])
        for query in queries_in_folder:
            clients_dict[query['name'].lower()] = query['id']
        return clients_dict
    except requests.RequestException as e:
        print(f"HTTP Error occurred: {str(e)}")
        return None
    except KeyError as e:
        print(f"Key error occurred: {str(e)}")
        return None


def get_query_id_by_path():
    query_path = "Shared Queries/Team/Support/Clients"
    encoded_pat = str(base64.b64encode(bytes(':' + TFS_PASSWORD, 'utf-8')), 'utf-8')
    headers = {
        'Authorization': 'Basic ' + encoded_pat
    }
    query_url = f"{TFS_URL}/{BMS_PROJECT_NAME}/_apis/wit/queries/{query_path}?api-version=6.0&$depth=2"

    response = requests.get(query_url, headers=headers)
    if response.status_code == 200:
        query_id = response.json()["id"]
        return query_id
    else:
        print(f"Failed to get query ID: {response.status_code} {response.text}")
        return None


def get_work_items_from_query(query_id):
    encoded_pat = str(base64.b64encode(bytes(':' + TFS_PASSWORD, 'utf-8')), 'utf-8')
    headers = {
        'Authorization': 'Basic ' + encoded_pat
    }
    query_results_url = f"{TFS_URL}/{BMS_PROJECT_NAME}/_apis/wit/wiql/{query_id}?api-version=6.0"

    response = requests.get(query_results_url, headers=headers)
    if response.status_code == 200:
        work_item_ids = [wi['id'] for wi in response.json().get('workItems', [])]
        return work_item_ids
    else:
        print(f"Failed to get work items from query: {response.status_code} {response.text}")
        return None

if __name__ == "__main__":
    print(get_query_id_by_path())
