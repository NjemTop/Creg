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


class PipelineStatusError(Exception):
    """Исключение для ошибок в статусе пайплайна."""
    pass

def get_pipeline_run_status(run_id):
    """
    Получает статус пайплайна из Azure DevOps.

    :param run_id: Идентификатор пайплайна, статус которого необходимо проверить.
    :type run_id: str
    :return: Статус пайплайна, если запрос успешен.
    :rtype: str
    :raises PipelineStatusError: Выбрасывает исключение, если запрос завершается ошибкой.

    Функция делает HTTP GET запрос к Azure DevOps API и возвращает статус пайплайна.
    Если ответ сервера не содержит успешного статуса (200), генерируется исключение с описанием ошибки.
    """
    url = f'{TFS_URL}/_apis/build/Builds/{run_id}?api-version=6.0-preview.1'
    
    encoded_pat = str(base64.b64encode(bytes(':' + TFS_PASSWORD, 'utf-8')), 'utf-8')
    headers = {'Authorization': 'Basic ' + encoded_pat}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result['status']
    else:
        error_msg = f"Ошибка при получении статуса пайплайна: {response.text}"
        scripts_error_logger.error(error_msg)
        raise PipelineStatusError(error_msg)


def monitor_pipeline_completion(run_id):
    """
    Проверяет завершение пайплайна, делая несколько попыток получить его статус.

    :param run_id: Идентификатор пайплайна для мониторинга.
    :type run_id: str
    :return: True, если пайплайн успешно завершен, False в случае ошибки или если пайплайн не завершился успешно.
    :rtype: bool

    Функция делает до 10 попыток получить статус пайплайна с интервалом в 10 минут.
    В случае успешного завершения пайплайна (статус 'succeeded' или 'partiallySucceeded'), возвращает True.
    Если пайплайн завершается с ошибкой или если достигнуто максимальное количество попыток, возвращает False.
    В процессе мониторинга логирует все значимые события и ошибки.
    """
    max_attempts = 10
    retry_delay = 600
    attempt = 0

    while attempt < max_attempts:
        try:
            status = get_pipeline_run_status(run_id)
            if status == 'succeeded':
                scripts_info_logger.info(f'Пайплайн с ID {run_id} успешно завершён.')
                return True
            elif status == 'failed':
                scripts_error_logger.error(f'Пайплайн с ID {run_id} завершился с ошибкой.')
                return False
            elif status == 'partiallySucceeded':
                scripts_info_logger.warning(f'Пайплайн с ID {run_id} выполнен с некритическими ошибками.')
                return True
            elif status == 'inProgress' or status == 'notStarted':
                scripts_info_logger.info(f'Пайплайн с ID {run_id} в состоянии "{status}". Проверка будет повторена.')
            else:
                scripts_error_logger.error(f'Пайплайн с ID {run_id} находится в неизвестном статусе: {status}.')
                return False
        except PipelineStatusError as error_message:
            scripts_error_logger.error(f"Ошибка статуса при попытке {attempt + 1}: {str(error_message)}")
            if attempt >= max_attempts - 1:
                scripts_error_logger.error(f"Пайплайн с ID {run_id} не удалось проверить после {max_attempts} попыток.")
                return False
            else:
                scripts_info_logger.info(f"Попытка {attempt + 1} из {max_attempts}. Следующая попытка через {retry_delay // 60} минут.")
        
        time.sleep(retry_delay)  # Ожидание перед следующей попыткой
        attempt += 1

    scripts_error_logger.error(f'Пайплайн с ID {run_id} не завершился в течение ожидаемого времени после {max_attempts} попыток.')
    return False
