from scripts.email.email_send import EmailService


class FakeClient:
    def __init__(self, client_name, short_name, password):
        self.client_name = client_name
        self.short_name = short_name
        self.password = password

def send_test_email():
    # Создаем экземпляр имитирующего клиента
    client_instance = FakeClient(
        'Тестовый клиент',
        'Тестовая учётная запись',
        'Тестовый пароль',
    )
    
    # Имитация технической информации (можете использовать словарь или класс, аналогично клиенту)
    tech_info = {
        'server_version': '2.45.36044.26900',
    }

    # Список словарей с данными контактов
    contact_data = [
        {'firstname': 'Иван', 'lastname': 'Иванов', 'contact_position': 'Администратор', 'contact_email': 'ivan@example.com'},
    ]

    # Словарь с информацией о модулях
    module_data = {
        'Трансляция': True,
        'Электронная подпись': True,
        'Поручения': True,
    }

    email_service = EmailService()

    # Вызов функции отправки с тестовыми данными
    email_service.send_client_creation_email(client_instance, tech_info, contact_data, module_data)
