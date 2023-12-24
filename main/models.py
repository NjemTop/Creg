from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid
from django.core.files.storage import FileSystemStorage
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
import os
import logging


logger = logging.getLogger(__name__)

backup_storage = FileSystemStorage(location='./backup/db/')

def backup_file_path(instance, filename):
    # Просто возвращаем имя файла, так как путь к директории уже задан в FileSystemStorage
    return filename

class BackupStorage(FileSystemStorage):
    def get_available_name(self, name, **kwargs):
        if self.exists(name):
            os.remove(self.path(name))
        return name

def generate_unique_id():
    """Функция генерации случайного числа для БД"""
    return str(uuid.uuid4())


class DatabaseBackup(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to=backup_file_path, storage=backup_storage, null=True, blank=True)
    is_selected = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Резервное копирование базы данных"
        verbose_name_plural = "Резервное копирование базы данных"
        db_table = 'databasebackup'

    def __str__(self):
        return self.file_name

@receiver(pre_delete, sender=DatabaseBackup)
def delete_backup_file(sender, instance, **kwargs):
    if instance.file:
        logger.info(f"Удаление файла бэкапа: {instance.file.name}")
        instance.file.storage.delete(instance.file.name)


class Favicon(models.Model):
    file = models.FileField(upload_to='favicons/')

    class Meta:
        verbose_name = "Изображения"
        verbose_name_plural = "Картинки"
        db_table = 'Favicon'

    def __str__(self):
        return self.file.name

@receiver(pre_delete, sender=Favicon)
def delete_favicon_file(sender, instance, **kwargs):
    if instance.file:
        path = instance.file.path
        if os.path.exists(path):
            os.remove(path)

@receiver(pre_save, sender=Favicon)
def update_favicon_file(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_favicon = Favicon.objects.get(pk=instance.pk)
        if old_favicon.file:
            old_path = old_favicon.file.path
            if os.path.exists(old_path):
                os.remove(old_path)
    except Favicon.DoesNotExist:
        return False

class ReleaseInfo(models.Model):
    """Таблица с информацией о рассылки клиенту"""
    date = models.DateField(verbose_name="Дата рассылки")
    release_number = models.CharField(verbose_name="Номер релиза", max_length=10)
    client_name = models.CharField(verbose_name="Наименование клиента", max_length=100)
    main_contact = models.CharField(verbose_name="Основной контакт", max_length=100)
    copy_contact = models.TextField(verbose_name="Копия", null=True, blank=True)

    class Meta:
        verbose_name = "Отчёт о рассылке"
        verbose_name_plural = "Отчёты о рассылке"
        db_table = "release_info"

    def __str__(self):
        return self.release_number


class ReportTicket(models.Model):
    """Класс для таблицы БД информации с отчётами о тикетах"""
    report_date = models.DateField(verbose_name='Дата отчёта', null=True, blank=True)
    ticket_id = models.IntegerField(verbose_name='Номер тикета', null=True, blank=True)
    subject = models.CharField(verbose_name='Тема тикета', max_length=100, null=True, blank=True)
    creation_date = models.DateField(verbose_name='Создан', null=True, blank=True)
    status = models.CharField(verbose_name='Статус', max_length=100, null=True, blank=True)
    client_name = models.CharField(verbose_name='Название клиента', max_length=100, null=True, blank=True)
    initiator = models.CharField(verbose_name='Инициатор', max_length=100, null=True, blank=True)
    priority = models.CharField(verbose_name='Приоритет', max_length=100, null=True, blank=True)
    assignee_name = models.CharField(verbose_name='Исполнитель', max_length=100, null=True, blank=True)
    updated_at = models.DateField(verbose_name='Дата обновления', null=True, blank=True)
    last_reply_at = models.DateField(verbose_name='Дата последнего ответа клиенту', null=True, blank=True)
    sla = models.BooleanField(verbose_name='SLA', null=True, blank=True)
    sla_time = models.IntegerField(verbose_name='Общее_время SLA', null=True, blank=True)
    response_time = models.IntegerField(verbose_name='Среднее время ответа', null=True, blank=True)
    cause = models.CharField(verbose_name='Причина возникновения', max_length=100, null=True, blank=True)
    module_boardmaps = models.CharField(verbose_name='Модуль BoardMaps', max_length=100, null=True, blank=True)
    staff_message = models.IntegerField(verbose_name='Сообщений от саппорта', null=True, blank=True)

    class Meta:
        verbose_name = "Отчёт о тикетах"
        verbose_name_plural = "Отчёты о тикетах"
        db_table = "report_ticket"

    def __str__(self):
        return str(self.ticket_id) if self.ticket_id else ''

class ReportDownloadjFrog(models.Model):
    """Класс для таблицы БД информации о скачивании с jFrog"""
    date = models.DateField(verbose_name='Дата')
    account_name = models.CharField(verbose_name='Учётная запись jFrog', max_length=100, null=True, blank=True)
    version_download = models.CharField(verbose_name='Версия скачивания', max_length=100, null=True, blank=True)
    ip_address = models.CharField(verbose_name='IP-адрес', max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = "Отчёт о скачивании с jFrog"
        verbose_name_plural = "Отчёты о скачивании с jFrog"
        db_table = "report_download_jfrog"

    def __str__(self):
        return str(self.date) if self.date else ''

class UsersBoardMaps(models.Model):
    """Таблица для пользователей сотрудников BoardMaps"""
    name = models.CharField(verbose_name='Сотрудник', max_length=150, null=True, blank=True)
    email = models.CharField(verbose_name='Почта', max_length=100, null=True, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=100, null=True, blank=True)
    test_automatic_email = models.BooleanField(verbose_name='Тестовая отправка рассылки', null=True, blank=True)
    new_client = models.BooleanField(verbose_name='Отправка информамции о новом созданном клиенте', null=True, blank=True)

    class Meta:
        verbose_name = "Сотрудники BoardMaps"
        verbose_name_plural = "Список сотрудников BoardMaps"
        db_table = "users_boardmaps"

    def __str__(self):
        return str(self.name) if self.name else ''

    @staticmethod
    def get_managers():
        return UsersBoardMaps.objects.filter(position='Менеджер')


class ClientsList(models.Model):
    client_name = models.CharField(verbose_name="Название клиента", max_length=100, db_index=True)
    short_name = models.CharField(verbose_name="Сокращенное наименование клиента", max_length=20, null=True, blank=True)
    password = models.CharField(verbose_name="Пароль для JFrog", max_length=20, null=True, blank=True)
    contact_status = models.BooleanField(verbose_name='Статус клиента', default=True)
    service = models.CharField(verbose_name="Обслуживание", max_length=255, default=generate_unique_id)
    technical_information = models.CharField(verbose_name="Техническая информация", max_length=255,
                                             default=generate_unique_id)
    integration = models.CharField(verbose_name="Интеграции", max_length=255, default=generate_unique_id)
    documents = models.CharField(verbose_name="Документы", max_length=255, default=generate_unique_id)
    notes = models.TextField(verbose_name="Примечание", null=True, blank=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Список клиентов"
        db_table = 'clients_list'

    def __str__(self):
        return self.client_name


class ClientsCard(models.Model):
    client_info = models.OneToOneField(ClientsList, on_delete=models.CASCADE, verbose_name='Client_info',
                                       related_name='clients_card')
    contacts = models.CharField(verbose_name='Контакты клиента', max_length=255, default=generate_unique_id)
    tech_notes = models.CharField(verbose_name='Технические заметки', max_length=255, default=generate_unique_id)
    connect_info = models.CharField(verbose_name='Информация для подключения', max_length=255, default=generate_unique_id)
    rdp = models.CharField(verbose_name='Удалённый доступ', max_length=255, default=generate_unique_id)
    tech_account = models.CharField(verbose_name='Технологическая учётная запись', max_length=255, default=generate_unique_id)
    bm_servers = models.CharField(verbose_name='Серверы BoardMaps', max_length=255, default=generate_unique_id)

    class Meta:
        verbose_name = "Карточка клиента"
        verbose_name_plural = "Список карточек клиентов"
        db_table = 'clients_card'

    def __str__(self):
        return str(self.client_info.id)


class ContactsCard(models.Model):
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name='contact_cards',
                                    verbose_name="Client Card")
    contact_name = models.CharField(verbose_name="ФИО", max_length=255)
    contact_position = models.CharField(verbose_name="Должность", max_length=255, null=True, blank=True)
    contact_email = models.EmailField(verbose_name="Почта", max_length=255)
    contact_number = models.CharField(verbose_name="Телефон", max_length=255, null=True, blank=True)
    notification_update = models.CharField(verbose_name="Отправка рассылки", max_length=255, null=True, blank=True)
    contact_notes = models.TextField(verbose_name="Примечание", null=True, blank=True)

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
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name='connect_info_card',
                                  verbose_name="Client Card")
    contact_info_name = models.CharField(verbose_name='ФИО', max_length=255)
    contact_info_account = models.CharField(verbose_name='Учетная запись', max_length=255)
    contact_info_password = models.CharField(verbose_name='Пароль', max_length=100)

    class Meta:
        verbose_name = "УЗ для подключения"
        verbose_name_plural = "Список УЗ для подключения"
        db_table = 'connect_info_card'

    def __str__(self):
        return f"{self.contact_info_name} ({self.client_card.client_info.client_name})"

    def set_password(self, raw_password):
        self.contact_info_password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.contact_info_password)


class BMServersCard(models.Model):
    """Серверы ВМ"""
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name="bm_servers_card",
                                    verbose_name="Client Card")
    bm_servers_circuit = models.CharField(verbose_name="Контур", max_length=100)
    bm_servers_servers_name = models.CharField(verbose_name="Имя сервера", max_length=100)
    bm_servers_servers_adress = models.CharField(verbose_name="Адрес сервера", max_length=100)
    bm_servers_operation_system = models.CharField(verbose_name="Операционная система", null=True, blank=True, max_length=100)
    bm_servers_url = models.CharField(verbose_name="URL", null=True, blank=True, max_length=100)
    bm_servers_role = models.CharField(verbose_name="Роль", max_length=100)

    class Meta:
        verbose_name = "Сервер ВМ"
        verbose_name_plural = "Серверы ВМ"
        db_table = "bm_servers_card"

    def __str__(self):
        return f"{self.bm_servers_servers_name} ({self.client_card.client_info.client_name})"


class Integration(models.Model):
    """Класс имеющихся интеграций у клиентов в системе BoardMaps"""
    client_card = models.OneToOneField(ClientsCard, on_delete=models.CASCADE, related_name="integration",
                                    verbose_name="Client Card")
    elasticsearch = models.BooleanField(verbose_name='ElasticSearch', null=True, blank=True, default=False)
    ad = models.BooleanField(verbose_name='Active Directory', null=True, blank=True, default=False)
    adfs = models.BooleanField(verbose_name='ADFS', null=True, blank=True, default=False)
    oauth_2 = models.BooleanField(verbose_name='OAuth 2.0', null=True, blank=True, default=False)
    module_translate = models.BooleanField(verbose_name='Модуль трансляции', null=True, blank=True, default=False)
    ms_oos = models.BooleanField(verbose_name='MS OOS', null=True, blank=True, default=False)
    exchange = models.BooleanField(verbose_name='Exchange', null=True, blank=True, default=False)
    office_365 = models.BooleanField(verbose_name='Office 365', null=True, blank=True, default=False)
    sfb = models.BooleanField(verbose_name='Skype For Business', null=True, blank=True, default=False)
    zoom = models.BooleanField(verbose_name='Zoom', null=True, blank=True, default=False)
    teams = models.BooleanField(verbose_name='Teams', null=True, blank=True, default=False)
    smtp = models.BooleanField(verbose_name='SMTP', null=True, blank=True, default=False)
    cryptopro_dss = models.BooleanField(verbose_name='Crypto_DSS', null=True, blank=True, default=False)
    cryptopro_csp = models.BooleanField(verbose_name='Crypto_CSP', null=True, blank=True, default=False)
    smpp = models.BooleanField(verbose_name='SMPP', null=True, blank=True, default=False)
    limesurvey = models.BooleanField(verbose_name='Анкетирование', null=True, blank=True, default=False)

    class Meta:
        verbose_name = "Интеграция"
        verbose_name_plural = "Интеграции"
        db_table = "integration"

    def __str__(self):
        return f"{self.client_card} ({self.client_card.client_info.client_name})"


class ModuleCard(models.Model):
    """Класс имеющихся модулей у клиентов в системе BoardMaps"""
    client_card = models.OneToOneField(ClientsCard, on_delete=models.CASCADE, related_name="module",
                                    verbose_name="Client Card")
    translate = models.BooleanField(verbose_name='Трансляция', null=True, blank=True, default=False)
    electronic_signature = models.BooleanField(verbose_name='Электронная подпись', null=True, blank=True, default=False)
    action_items = models.BooleanField(verbose_name='Поручения', null=True, blank=True, default=False)
    limesurvey = models.BooleanField(verbose_name='Анкетирование', null=True, blank=True, default=False)
    advanced_voting = models.BooleanField(verbose_name='Расширенные сценарии голосования', null=True, blank=True, default=False)
    advanced_work_with_documents = models.BooleanField(verbose_name='Расширенные сценарии работы с документами', null=True, blank=True, default=False)
    advanced_access_rights_management = models.BooleanField(verbose_name='Расширенные сценарии управления правами доступа', null=True, blank=True, default=False)
    visual_improvements = models.BooleanField(verbose_name='Визуальные улучшения', null=True, blank=True, default=False)
    third_party_product_integrations = models.BooleanField(verbose_name='Интеграции со сторонними продуктами', null=True, blank=True, default=False)
    microsoft_enterprise_product_integrations = models.BooleanField(verbose_name='Интеграция с продуктами Microsoft Enterprise', null=True, blank=True, default=False)
    microsoft_office_365_integration = models.BooleanField(verbose_name='Интеграция с продуктами Microsoft Office 365', null=True, blank=True, default=False)

    class Meta:
        verbose_name = "Модули"
        verbose_name_plural = "Список модулей"
        db_table = "module"

    def __str__(self):
        return f"{self.client_card} ({self.client_card.client_info.client_name})"


class TechAccountCard(models.Model):
    """
    Класс таблицы БД с техническими учётными записями клиента
    """
    client_card = models.ForeignKey(ClientsCard, on_delete=models.CASCADE, related_name='tech_account_card',
                                  verbose_name="Client Card")
    contact_info_disc = models.CharField(verbose_name='Описание', max_length=255)
    contact_info_account = models.CharField(verbose_name='Учетная запись', max_length=255)
    contact_info_password = models.CharField(verbose_name='Пароль', max_length=255)

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


class ConnectionInfo(models.Model):
    client_card = models.OneToOneField(ClientsCard, on_delete=models.CASCADE, related_name='connection_info', null=True)
    file_path = models.FileField(upload_to='uploaded_files/')
    text = models.TextField(null=True)

    class Meta:
        verbose_name = "Удалёнка клиента"
        verbose_name_plural = "Информация по подключению к клиенту"
        db_table = 'connection_info'

    def __str__(self):
        return f"File {self.file_path} for client {self.client_card.client_info.client_name}"


class ServiseCard(models.Model):
    """
    Таблица с информацией обслуживания клиента.
    """
    client_card = models.OneToOneField(ClientsCard, on_delete=models.CASCADE, related_name='servise_card',
                                    verbose_name="Client Card")
    service_pack = models.CharField(verbose_name="Тарифный план", max_length=255)
    manager = models.CharField(verbose_name="Менеджер", max_length=255)
    manager_new = models.ForeignKey(UsersBoardMaps, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'position': 'Менеджер'}, verbose_name="Менеджер")
    loyal = models.CharField(verbose_name="Лояльность", max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Обслуживание клиента"
        verbose_name_plural = "Список обслуживание клиентов"
        db_table = 'servise_card'

    def __str__(self):
        return f"{self.service_pack} ({self.client_card.client_info.client_name})"


class TechInformationCard(models.Model):
    """
    Таблица с технической информацией клиента.
    """
    client_card = models.OneToOneField(ClientsCard, on_delete=models.CASCADE, related_name='tech_information',
                                    verbose_name="Client Card")
    server_version = models.CharField(verbose_name="Версия сервера", max_length=255)
    update_date = models.DateField(verbose_name="Дата обновления", max_length=255)
    api = models.BooleanField(verbose_name="API", null=True, blank=True, default=False)
    ipad = models.CharField(verbose_name="iPad", max_length=255, null=True, blank=True)
    android = models.CharField(verbose_name="Android", max_length=255, null=True, blank=True)
    mdm = models.CharField(verbose_name="MDM", max_length=255, null=True, blank=True)
    localizable_web = models.BooleanField(verbose_name="Локализация Web", null=True, blank=True, default=False)
    localizable_ios = models.BooleanField(verbose_name="Локализация iOS", null=True, blank=True, default=False)
    skins_web = models.BooleanField(verbose_name="Скины Web", null=True, blank=True, default=False)
    skins_ios = models.BooleanField(verbose_name="Скины iOS", null=True, blank=True, default=False)

    class Meta:
        verbose_name = "Техническая информация клиента"
        verbose_name_plural = "Список технической информации клиентов"
        db_table = 'tech_information'

    def __str__(self):
        return f"{self.server_version} ({self.client_card.client_info.client_name})"

class TechNote(models.Model):
    """
    Таблица с техническими заметками клиента.
    """
    client_card = models.OneToOneField(ClientsCard, on_delete=models.CASCADE, related_name='tech_note',
                                    verbose_name="Client Card")
    tech_note_text = models.TextField(verbose_name="Технические заметки", null=True, blank=True)

    class Meta:
        verbose_name = "Технические заметки клиента"
        verbose_name_plural = "Список технических заметок клиентов"
        db_table = 'tech_note'

    def __str__(self):
        return f"{self.client_card} ({self.client_card.client_info.client_name})"
