from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid


def generate_unique_id():
    """Функция генерации случайного числа для БД"""
    return str(uuid.uuid4())


class Favicon(models.Model):
    file = models.FileField(upload_to='favicons/')

    class Meta:
        verbose_name = "Изображения"
        verbose_name_plural = "Картинки"
        db_table = 'Favicon'

    def __str__(self):
        return self.file.name


class ClientsList(models.Model):
    client_name = models.CharField(verbose_name="Client_name", max_length=255, db_index=True)
    contact_status = models.BooleanField(verbose_name='Contact Status', default=True)
    service = models.CharField(verbose_name="Service", max_length=255, default=generate_unique_id)
    technical_information = models.CharField(verbose_name="Technical_information", max_length=255,
                                             default=generate_unique_id)
    integration = models.CharField(verbose_name="Integration", max_length=255, default=generate_unique_id)
    documents = models.CharField(verbose_name="Documents", max_length=255, default=generate_unique_id)
    notes = models.TextField(verbose_name="Notes", null=True, blank=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Список клиентов"
        db_table = 'clients_list'

    def __str__(self):
        return self.client_name


class ClientsCard(models.Model):
    client_info = models.OneToOneField(ClientsList, on_delete=models.CASCADE, verbose_name='Client_info',
                                       related_name='clients_card')
    contacts = models.CharField(verbose_name='Contacts', max_length=255, default=generate_unique_id)
    tech_notes = models.CharField(verbose_name='Tech_notes', max_length=255, default=generate_unique_id)
    connect_info = models.CharField(verbose_name='Connect_info', max_length=255, default=generate_unique_id)
    rdp = models.CharField(verbose_name='RDP', max_length=255, default=generate_unique_id)
    tech_account = models.CharField(verbose_name='Tech_account', max_length=255, default=generate_unique_id)
    bm_servers = models.CharField(verbose_name='BM_servers', max_length=255, default=generate_unique_id)

    class Meta:
        verbose_name = "Карточка клиента"
        verbose_name_plural = "Список карточек клиентов"
        db_table = 'clients_card'

    def __str__(self):
        return str(self.client_info.id)


class ContactsCard(models.Model):
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name='contact_cards',
                                    verbose_name="Client Card")
    contact_name = models.CharField(verbose_name="contact_name", max_length=255)
    contact_position = models.CharField(verbose_name="contact_position", max_length=255, null=True, blank=True)
    contact_email = models.EmailField(verbose_name="contact_email", max_length=255)
    notification_update = models.CharField(verbose_name="notification_update", max_length=255, null=True, blank=True)
    contact_notes = models.TextField(verbose_name="contact_notes", null=True, blank=True)

    class Meta:
        verbose_name = "Контакт клиента"
        verbose_name_plural = "Список контактов клиентов"
        db_table = 'contacts_card'

    def __str__(self):
        return f"{self.contact_name} ({self.client_card.client_info.client_name})"


class ConnectInfoCard(models.Model):
    """
    Класс таблицы БД с учётными записями информации о подключении к клиенту
    """
    client_id = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name='connect_info_card',
                                  verbose_name="Client Card")
    contact_info_name = models.TextField(verbose_name='ФИО')
    contact_info_account = models.TextField(verbose_name='Учетная_запись')
    contact_info_password = models.TextField(verbose_name='Пароль')

    class Meta:
        verbose_name = "УЗ для подключения"
        verbose_name_plural = "Список УЗ для подключения"
        db_table = 'connect_info_card'

    def __str__(self):
        return f"{self.contact_info_name} ({self.client_id.client_info.client_name})"

    def set_password(self, raw_password):
        self.contact_info_password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.contact_info_password)


class BMServersCard(models.Model):
    """Серверы ВМ"""
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name="bm_servers_card",
                                    verbose_name="Client Card")
    bm_servers_circuit = models.CharField(verbose_name="Circuit", max_length=100)
    bm_servers_servers_name = models.CharField(verbose_name="Server_name", max_length=100)
    bm_servers_servers_adress = models.CharField(verbose_name="Server_ip_adress", max_length=100)
    bm_servers_operation_system = models.CharField(verbose_name="OS", null=True, blank=True, max_length=100)
    bm_servers_url = models.CharField(verbose_name="URL", null=True, blank=True, max_length=100)
    bm_servers_role = models.CharField(verbose_name="Role", max_length=100)

    class Meta:
        verbose_name = "Сервер ВМ"
        verbose_name_plural = "Серверы ВМ"
        db_table = "bm_servers_card"

    def __str__(self):
        return f"{self.bm_servers_servers_name} ({self.client_card.client_info.client_name})"


class Integration(models.Model):
    """Класс имеющихся интеграций у клиентов в системе BoardMaps"""
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name="integration",
                                    verbose_name="Client Card")
    elasticsearch = models.BooleanField(verbose_name='Elasticsearch', null=True, blank=True)
    ad = models.BooleanField(verbose_name='AD', null=True, blank=True)
    adfs = models.BooleanField(verbose_name='ADFS', null=True, blank=True)
    oauth_2 = models.BooleanField(verbose_name='OAuth_2.0', null=True, blank=True)
    module_translate = models.BooleanField(verbose_name='Модуль_трансляции', null=True, blank=True)
    ms_oos = models.BooleanField(verbose_name='MS OOS', null=True, blank=True)
    exchange = models.BooleanField(verbose_name='Exchange', null=True, blank=True)
    office_365 = models.BooleanField(verbose_name='Office_365', null=True, blank=True)
    sfb = models.BooleanField(verbose_name='Skype_For_Business', null=True, blank=True)
    zoom = models.BooleanField(verbose_name='Zoom', null=True, blank=True)
    teams = models.BooleanField(verbose_name='Teams', null=True, blank=True)
    smtp = models.BooleanField(verbose_name='SMTP', null=True, blank=True)
    cryptopro_dss = models.BooleanField(verbose_name='Cripto_DSS', null=True, blank=True)
    cryptopro_csp = models.BooleanField(verbose_name='Cripto_CSP', null=True, blank=True)
    smpp = models.BooleanField(verbose_name='SMPP', null=True, blank=True)
    limesurvey = models.BooleanField(verbose_name='Анкетирование', null=True, blank=True)

    class Meta:
        verbose_name = "Интеграция"
        verbose_name_plural = "Интеграции"
        db_table = "integration"

    def __str__(self):
        return f"{self.client_card} ({self.client_card.client_info.client_name})"


class TechAccountCard(models.Model):
    """
    Класс таблицы БД с техническими учётными записями клиента
    """
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name='tech_account_card',
                                  verbose_name="Client Card")
    contact_info_disc = models.TextField(verbose_name='Описание')
    contact_info_account = models.TextField(verbose_name='Учетная_запись')
    contact_info_password = models.TextField(verbose_name='Пароль')

    class Meta:
        verbose_name = "Тех. УЗ клиента"
        verbose_name_plural = "Список тех. УЗ клиентов"
        db_table = 'tech_account_card'

    def __str__(self):
        return f"{self.contact_info_disc} ({self.client_card.client_info.client_name})"

    def set_password(self, raw_password):
        self.contact_info_password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.contact_info_password)
