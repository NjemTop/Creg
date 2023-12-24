import re
from datetime import datetime, timedelta
import pytz
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

utc=pytz.UTC

def analyze_logs_and_get_data():
    log_file_path = os.path.abspath("./scripts/artifactory_downloads_log/artifactory-request.log")
    
    if not os.path.exists(log_file_path):
        return "Файл журнала не существует", []

    pattern = re.compile(r"(\S{24})\|.*?(\S+)\|(\S+)\|(\S+)\|HEAD\|/api/docker/public/v2/[\w-]+/manifests/([\d.]+)")

    client_data_list = []
    current_date = datetime.now().replace(tzinfo=utc)
    two_days_ago = (current_date - timedelta(days=2)).replace(tzinfo=utc)
    
    with open(log_file_path, 'r') as file:
        for line in file:
            match = pattern.search(line)
            if match:
                logger.info(f'Строка подходит под регулярку: {match.group()}')
                log_date_str = match.group(1)
                if log_date_str:
                    log_date = datetime.fromisoformat(log_date_str.replace("Z", "+00:00"))
                    logger.info(f'Дата этой строки: {log_date}')
                    
                    if log_date >= two_days_ago:
                        account_name = match.group(4)
                        version = match.group(5)
                        logger.info(f'УЗ: {account_name}, Версии: {version}')
                        client_data_list.append({"account_name": account_name, "version": version})
                    
    return "Успешно", client_data_list

# Для проверки работы
if __name__ == "__main__":
    status, data = analyze_logs_and_get_data()
    print(f"Статус: {status}")
    print(f"Данные: {data}")
