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


class СonnectInfoCard(models.Model):
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
