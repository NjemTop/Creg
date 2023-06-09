from django.test import TestCase
from main.models import (
    ClientsList,
    ClientsCard,
    TechInformationCard,
    ContactsCard,
    ConnectInfoCard,
    BMServersCard,
    Integration,
    ModuleCard,
    TechAccountCard,
    ConnectionInfo,
    ServiseCard,
)

class ContactsCardTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        contacts_card = ContactsCard.objects.create(
            client_card=client_card,
            contact_name="ФИО",
            contact_position="Должность",
            contact_email="contact@example.com",
            notification_update="Основной",
            contact_notes="Заметки",
        )
        print(f"Контакт создан: {contacts_card}")

    def test_str_representation(self):
        contacts_card = ContactsCard.objects.first()
        self.assertEqual(
            str(contacts_card),
            "ФИО (Тестовое имя клиента)"
        )

class ConnectInfoCardTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        connect_info_card = ConnectInfoCard.objects.create(
            client_card=client_card,
            contact_info_name="ФИО",
            contact_info_account="Имя УЗ",
            contact_info_password="Пароль",
        )
        print(f"Создана информация о подключении: {connect_info_card}")

    def test_str_representation(self):
        connect_info_card = ConnectInfoCard.objects.first()
        self.assertEqual(
            str(connect_info_card),
            "ФИО (Тестовое имя клиента)"
        )

class BMServersCardTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        bm_servers_card = BMServersCard.objects.create(
            client_card=client_card,
            bm_servers_circuit="Прод",
            bm_servers_servers_name="Web.corp.base",
            bm_servers_servers_adress="192.168.88.12",
            bm_servers_operation_system="Windows Server 2019",
            bm_servers_url="https://example.com",
            bm_servers_role="Вэб",
        )
        print(f"Сервер создан: {bm_servers_card}")

    def test_str_representation(self):
        bm_servers_card = BMServersCard.objects.first()
        self.assertEqual(
            str(bm_servers_card),
            "Web.corp.base (Тестовое имя клиента)"
        )

class IntegrationTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        integration = Integration.objects.create(
            client_card=client_card,
            elasticsearch=True,
            ad=True,
            adfs=True,
            oauth_2=True,
            module_translate=True,
            ms_oos=True,
            exchange=True,
            office_365=True,
            sfb=True,
            zoom=True,
            teams=True,
            smtp=True,
            cryptopro_dss=True,
            cryptopro_csp=True,
            smpp=True,
            limesurvey=True,
        )
        print(f"Интеграция созданач : {integration}")

    def test_str_representation(self):
        integration = Integration.objects.first()
        self.assertEqual(
            str(integration),
            f"{integration.client_card} (Тестовое имя клиента)"
        )

class ModuleCardTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        module_card = ModuleCard.objects.create(
            client_card=client_card,
            translate=True,
            electronic_signature=True,
            action_items=True,
            limesurvey=True,
            advanced_voting=True,
            advanced_work_with_documents=True,
            advanced_access_rights_management=True,
            visual_improvements=True,
            third_party_product_integrations=True,
            microsoft_enterprise_product_integrations=True,
            microsoft_office_365_integration=True,
        )
        print(f"Модули созданы: {module_card}")

    def test_str_representation(self):
        module_card = ModuleCard.objects.first()
        self.assertEqual(
            str(module_card),
            f"{module_card.client_card} (Тестовое имя клиента)"
        )

class TechAccountCardTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        tech_account_card = TechAccountCard.objects.create(
            client_card=client_card,
            contact_info_disc="Инженер УЗ",
            contact_info_account="Логин",
            contact_info_password="Пароль",
        )
        print(f"Тех. УЗ созданы: {tech_account_card}")

    def test_str_representation(self):
        tech_account_card = TechAccountCard.objects.first()
        self.assertEqual(
            str(tech_account_card),
            f"{tech_account_card.contact_info_disc} (Тестовое имя клиента)"
        )

class ConnectionInfoTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        connection_info = ConnectionInfo.objects.create(
            client_card=client_card,
            file_path="path/to/file",
            text="Информация о подключении",
        )
        print(f"Создана информация о подключении: {connection_info}")

    def test_str_representation(self):
        connection_info = ConnectionInfo.objects.first()
        self.assertEqual(
            str(connection_info),
            f"File path/to/file for client Тестовое имя клиента"
        )

class ServiseCardTestCase(TestCase):
    def setUp(self):
        clients_list = ClientsList.objects.create(client_name="Тестовое имя клиента")
        client_card = ClientsCard.objects.create(client_info=clients_list)
        servise_card = ServiseCard.objects.create(
            client_card=client_card,
            service_pack="Сервис план",
            manager="Менеджер",
            loyal="Лояльность",
        )
        print(f"Информация об обслуживании создана: {servise_card}")

    def test_str_representation(self):
        servise_card = ServiseCard.objects.first()
        self.assertEqual(
            str(servise_card),
            f"{servise_card.service_pack} (Тестовое имя клиента)"
        )
