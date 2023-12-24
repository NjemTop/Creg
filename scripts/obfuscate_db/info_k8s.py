import paramiko
import re
import yaml

def get_postgresql_info(hostname, ssh_username, ssh_password, namespace='default', pod_name_starts_with='boardmaps-db'):
    """
    Получает информацию о базе данных PostgreSQL из файла values.yml на удаленном сервере с помощью SSH,
    а также узнаём имя пода в Kubernetes.

    :param hostname: Адрес удаленного сервера.
    :param ssh_username: Имя пользователя SSH.
    :param ssh_password: Пароль пользователя SSH.
    :param namespace: Пространство имен в Kubernetes, где запущен под.
    :param pod_name_starts_with: Начало имени пода, который нужно найти.
    :return: Словарь с данными о подключении к поду PostgreSQL или None в случае ошибки.
    """
    try:
        # Подключение по SSH к серверу Kubernetes
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname, username=ssh_username, password=ssh_password)

        # Выполнение команды sudo ls -la /root для просмотра содержимого домашней директории пользователя root
        stdin, stdout, stderr = ssh_client.exec_command('sudo ls -la /root')
        root_home_content = stdout.read().decode()

        # Проверка, содержит ли вывод содержимое файла values.yml
        if 'values.yml' not in root_home_content:
            print("Файл values.yml не найден в домашней директории пользователя root.")
            print("Содержимое домашней директории пользователя root:")
            print(root_home_content)
            return None

        # Выполнение команды sudo cat /root/values.yml для получения содержимого файла values.yml
        get_values_command = 'sudo cat /root/values.yml'
        stdin, stdout, stderr = ssh_client.exec_command(get_values_command)
        values_yaml = stdout.read().decode()

        # Парсинг YAML
        values_data = yaml.safe_load(values_yaml)

        # Извлечение данных о базе данных PostgreSQL
        postgres_data = values_data.get('db', {})
        postgres_db = postgres_data.get('postgresDb', '')
        postgres_user = postgres_data.get('postgresUser', '')
        postgres_password = postgres_data.get('postgresPassword', '')

        # Находим имя пода с БД
        stdin, stdout, stderr = ssh_client.exec_command(f'sudo kubectl get pods -n {namespace} -o name | grep {pod_name_starts_with}')
        # Проверим ошибки при выполнении команды kubectl
        errors = stderr.read().decode().strip()
        if errors:
            print(f"Ошибка при выполнении команды kubectl: {errors}")
            return None

        pod_name = stdout.read().decode().strip()
        if not pod_name:
            print(f"Под начинающийся на {pod_name_starts_with} не найден.")
            return None
        
        # Закрываем SSH-соединение
        ssh_client.close()

        # Возвращаем данные для подключения к поду
        return {
            'postgres_db': postgres_db,
            'postgres_user': postgres_user,
            'postgres_password': postgres_password,
            'pod_name': pod_name  # полное имя пода
        }
    except paramiko.AuthenticationException:
        print("Ошибка аутентификации по SSH.")
    except paramiko.SSHException as e:
        print(f"Ошибка SSH: {str(e)}")
    except Exception as e:
        print(f"Ошибка: {str(e)}")

    return None


# hostname = "SUP-KUBE-APP03p.corp.boardmaps.com"
# ssh_username = "ubuntu"
# ssh_password = "Public3772"

# postgres_info = get_postgresql_info(hostname, ssh_username, ssh_password)

# if postgres_info:
#     print("Информация о базе данных PostgreSQL:")
#     print(f"Database: {postgres_info['postgres_db']}")
#     print(f"User: {postgres_info['postgres_user']}")
#     print(f"Password: {postgres_info['postgres_password']}")
#     print(f"Pod_name: {postgres_info['pod_name']}")
