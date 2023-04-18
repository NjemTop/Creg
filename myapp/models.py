from django.db import models
import uuid

def generate_unique_id():
    """Функция генерации случайного числа для БД"""
    return str(uuid.uuid4())

class BMInfoOnClient(models.Model):
    client_name = models.TextField(verbose_name="Название клиента", db_index=True)
    contact_status = models.BooleanField(verbose_name="Активность")
    service = models.TextField(verbose_name="Обслуживание", default=generate_unique_id)
    technical_information = models.TextField(verbose_name="Тех информация", default=generate_unique_id)
    integration = models.TextField(verbose_name="Интеграции", default=generate_unique_id)
    documents = models.TextField(verbose_name="Документы", default=generate_unique_id)
    notes = models.CharField(verbose_name="Примечания", max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = "BM Info on Clients"
        db_table = 'bm_info_on_clients'

    def __str__(self):
        return self.client_name

class Favicon(models.Model):
    file = models.FileField(upload_to='favicons/') # Исправлен путь upload_to

    def __str__(self):
        return self.file.name
