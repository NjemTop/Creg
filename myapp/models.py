from django.db import models
import uuid

def generate_unique_id():
    """Функция генерации случайного числа для БД"""
    return str(uuid.uuid4())

class BMInfoOnClient(models.Model):
    client_name = models.CharField(verbose_name="Client_name", max_length=255, db_index=True)
    contact_status = models.BooleanField(verbose_name='Contact Status', default=True)
    service = models.CharField(verbose_name="Service", max_length=255, default=generate_unique_id)
    technical_information = models.CharField(verbose_name="Technical_information", max_length=255, default=generate_unique_id)
    integration = models.CharField(verbose_name="Integration", max_length=255, default=generate_unique_id)
    documents = models.CharField(verbose_name="Documents", max_length=255, default=generate_unique_id)
    notes = models.TextField(verbose_name="Notes", null=True, blank=True)

    class Meta:
        verbose_name_plural = "BM Info on Clients"
        db_table = 'bm_info_on_clients'

    def __str__(self):
        return self.client_name

class Favicon(models.Model):
    file = models.FileField(upload_to='favicons/')

    def __str__(self):
        return self.file.name

class ClientsCard(models.Model):
    client_info = models.OneToOneField(BMInfoOnClient, primary_key=True, on_delete=models.CASCADE, verbose_name='Client_info', related_name='clients_card')
    contacts = models.CharField(verbose_name='Contacts', max_length=255, default=generate_unique_id)
    tech_notes = models.CharField(verbose_name='Tech_notes', max_length=255, default=generate_unique_id)
    connect_info = models.CharField(verbose_name='Connect_info', max_length=255, default=generate_unique_id)
    rdp = models.CharField(verbose_name='RDP', max_length=255, default=generate_unique_id)
    tech_account = models.CharField(verbose_name='Tech_account', max_length=255, default=generate_unique_id)
    bm_servers = models.CharField(verbose_name='BM_servers', max_length=255, default=generate_unique_id)

    class Meta:
        verbose_name_plural = "Clients Cards"
        db_table = 'clients_card'

    def __str__(self):
        return f"Client {self.client_info.id}"
