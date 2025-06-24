from django.db import models
from simple_history.models import HistoricalRecords
from django.utils import timezone
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password, check_password
from apps.utils.passwords import generate_secure_password
from apps.utils.validators import validate_client_password


class Language(models.Model):
    """Языки клиентов и рассылок"""
    code = models.CharField(max_length=5, unique=True, verbose_name="Код языка")
    name = models.CharField(max_length=100, unique=True, verbose_name="Название языка")

    class Meta:
        verbose_name = "Язык"
        verbose_name_plural = "Языки"
        db_table = "language"

    def __str__(self):
        return self.name

    @staticmethod
    def initialize_languages():
        """Автоматическое заполнение таблицы `Language` стандартными значениями"""
        defaults = [
            {"code": "ru", "name": "Русский"},
            {"code": "en", "name": "Английский"},
        ]
        for lang in defaults:
            Language.objects.get_or_create(code=lang["code"], defaults={"name": lang["name"]})

class ServicePack(models.Model):
    """Тарифные планы обслуживания"""
    code = models.CharField(max_length=50, unique=True, verbose_name="Код")
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Тарифный план"
        verbose_name_plural = "Тарифные планы"
        db_table = "service_pack"

    def __str__(self):
        return self.name

    @staticmethod
    def initialize_default_packs():
        default_packs = [
            {"code": "bronze", "name": "Bronze"},
            {"code": "silver", "name": "Silver"},
            {"code": "gold", "name": "Gold"},
            {"code": "platinum", "name": "Platinum"},
        ]
        for pack in default_packs:
            ServicePack.objects.get_or_create(code=pack["code"], defaults={"name": pack["name"]})


class Client(models.Model):
    """ Клиенты """

    client_name = models.CharField(verbose_name="Полное наименовкние клиента", max_length=100, db_index=True, unique=True)
    short_name = models.CharField(verbose_name="Сокращённое наименование клиента", max_length=20, blank=True, unique=True)
    account_name = models.CharField(verbose_name="Учётная запись клиента", max_length=20, unique=True)
    password = models.CharField(verbose_name="Пароль для JFrog", max_length=20)
    contact_status = models.BooleanField(verbose_name='Статус клиента', default=False)
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Язык клиента")
    saas = models.BooleanField(verbose_name="Клиент на SaaS", default=False)
    modules = models.ManyToManyField("Module", through="ClientModule", verbose_name="Модули")
    integrations = models.ManyToManyField("Integration", through="ClientIntegration", verbose_name="Интеграции")
    notes = models.TextField(verbose_name="Примечание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Список клиентов"
        db_table = 'client'

    def __str__(self):
        return self.client_name

    def clean(self):
        if self.password:
            validate_client_password(self.password, self.client_name)

    def save(self, *args, **kwargs):
        if not self.password:
            self.password = generate_secure_password()
        self.full_clean()
        super().save(*args, **kwargs)

class Contact(models.Model):
    """Контакты клиентов"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contacts", verbose_name="Клиент")
    first_name = models.CharField(verbose_name="Имя", max_length=255)
    last_name = models.CharField(verbose_name="Фамилия", max_length=255)
    position = models.CharField(verbose_name="Должность", max_length=255, blank=True)
    email = models.EmailField(verbose_name="Почта", max_length=255, unique=True)
    phone_number = models.CharField(verbose_name="Основной телефон", max_length=20, blank=True)
    phone_number_extra = models.CharField(verbose_name="Дополнительный телефон", max_length=20, blank=True)
    notification_update = models.BooleanField(verbose_name="Получает рассылки", default=False)
    notes = models.TextField(verbose_name="Примечание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты клиентов"
        db_table = "contact"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.client.client_name})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class ServiceInfo(models.Model):
    """ Обслуживание клиента """
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="service_info", verbose_name="Клиент")
    service_pack = models.ForeignKey(
        "ServicePack",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Тарифный план"
    )
    manager = models.ForeignKey(
        "company.Employee",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Менеджер",
        limit_choices_to={'role': 'Менеджер'}
    )
    loyalty = models.CharField(verbose_name="Лояльность", max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Обслуживание клиента"
        verbose_name_plural = "Обслуживание клиентов"
        db_table = "service_info"

    def __str__(self):
        return f"{self.client.client_name} - {self.manager}"


class TechnicalInfo(models.Model):
    """ Техническая информация клиента """
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="technical_info", verbose_name="Клиент")
    
    server_version = models.CharField(verbose_name="Текущая версия сервера", max_length=255)
    previous_version = models.CharField(verbose_name="Предыдущая версия сервера", max_length=255, blank=True, null=True)
    
    update_date = models.DateField(verbose_name="Дата последнего обновления", default=timezone.now)
    previous_update_date = models.DateField(verbose_name="Дата предыдущего обновления", blank=True, null=True)
    
    api_enabled = models.BooleanField(verbose_name="API", default=False)
    mdm_support = models.BooleanField(verbose_name="MDM поддержка", default=False)
    
    supports_ipad = models.BooleanField(verbose_name="Поддержка iPad", default=False)
    supports_android = models.BooleanField(verbose_name="Поддержка Android", default=False)
    
    localized_web = models.BooleanField(verbose_name="Локализация Web", default=False)
    localized_ios = models.BooleanField(verbose_name="Локализация iOS", default=False)
    skins_web = models.BooleanField(verbose_name="Скины Web", default=False)
    skins_ios = models.BooleanField(verbose_name="Скины iOS", default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Техническая информация"
        verbose_name_plural = "Техническая информация клиентов"
        db_table = "technical_info"

    def __str__(self):
        return f"{self.client.client_name} - {self.server_version}"


class ServerVersionHistory(models.Model):
    """ История обновлений версий серверов """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="server_version_history", verbose_name="Клиент")
    
    version = models.CharField(verbose_name="Версия сервера", max_length=255)
    update_date = models.DateField(verbose_name="Дата обновления", default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История обновлений сервера"
        verbose_name_plural = "История обновлений серверов"
        db_table = "server_version_history"
        ordering = ["-update_date"]  # Сортировка по убыванию даты обновления

    def __str__(self):
        return f"{self.client.client_name} - {self.version} ({self.update_date})"


@receiver(pre_save, sender=TechnicalInfo)
def track_server_version_change(sender, instance, **kwargs):
    """
    Автоматически обновляет `previous_version` и `previous_update_date`,
    а также создаёт запись в `ServerVersionHistory`, если `server_version` изменилось.
    """
    if instance.pk:  # Проверяем, что объект уже существует в базе
        old_instance = sender.objects.get(pk=instance.pk)
        
        if old_instance.server_version != instance.server_version:
            # Сохраняем предыдущую версию
            instance.previous_version = old_instance.server_version
            instance.previous_update_date = old_instance.update_date
            
            # Добавляем запись в историю обновлений
            ServerVersionHistory.objects.create(
                client=instance.client,
                version=old_instance.server_version,
                update_date=old_instance.update_date
            )

            # Если `update_date` не задано вручную — ставим текущую дату
            if not instance.update_date or instance.update_date == old_instance.update_date:
                instance.update_date = timezone.now()


@receiver(post_save, sender=TechnicalInfo)
def save_version_history(sender, instance, created, **kwargs):
    """
    Автоматически добавляет новую запись в историю обновлений при каждом изменении версии.
    """
    if not created:  # Если это не новая запись, а обновление
        ServerVersionHistory.objects.create(
            client=instance.client,
            version=instance.server_version,
            update_date=instance.update_date
        )


class Module(models.Model):
    """ Доступные модули """
    name = models.CharField(max_length=255, unique=True, verbose_name="Название модуля")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"
        db_table = "module"

    def __str__(self):
        return self.name


class ClientModule(models.Model):
    """ Таблица связки Клиент → Модули (M2M) с доп. инфой """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, verbose_name="Модуль")
    is_active = models.BooleanField(default=True, verbose_name="Активен ли модуль?")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подключения")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Связь клиента и модуля"
        verbose_name_plural = "Связи клиентов и модулей"
        db_table = "client_module"
        unique_together = ("client", "module")  # Запрещает дублирование записей

    def __str__(self):
        return f"{self.client.client_name} - {self.module.name}"

class Integration(models.Model):
    """ Доступные интеграции """
    name = models.CharField(max_length=255, unique=True, verbose_name="Название интеграции")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Интеграция"
        verbose_name_plural = "Интеграции"
        db_table = "integration"

    def __str__(self):
        return self.name


class ClientIntegration(models.Model):
    """ Таблица связки Клиент → Интеграции (M2M) с доп. инфой """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, verbose_name="Интеграция")
    is_active = models.BooleanField(default=True, verbose_name="Активна ли интеграция?")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подключения")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Связь клиента и интеграции"
        verbose_name_plural = "Связи клиентов и интеграций"
        db_table = "client_integration"
        unique_together = ("client", "integration")  # Запрещает дублирование записей

    def __str__(self):
        return f"{self.client.client_name} - {self.integration.name}"


class Server(models.Model):
    """ Серверы клиента """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="servers", verbose_name="Клиент")
    circuit = models.CharField(verbose_name="Контур", max_length=100)
    name = models.CharField(verbose_name="Имя сервера", max_length=100)
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес", protocol='both', unpack_ipv4=True)
    operating_system = models.CharField(verbose_name="Операционная система", max_length=100, blank=True)
    url = models.URLField(verbose_name="URL", blank=True, null=True)
    platform = models.ForeignKey("Platform", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Платформа")
    role = models.ForeignKey("ServerRole", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Роль сервера")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Сервер"
        verbose_name_plural = "Серверы"
        db_table = "server"
        unique_together = ("client", "name")  # Запрещает дублировать серверы с одинаковыми именами

    def __str__(self):
        return f"{self.client.client_name} - {self.name} ({self.ip_address})"


class ServerRole(models.Model):
    """ Роли серверов """
    name = models.CharField(verbose_name="Название роли", max_length=100, unique=True)
    description = models.TextField(verbose_name="Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Роль сервера"
        verbose_name_plural = "Роли серверов"
        db_table = "server_role"

    def __str__(self):
        return self.name

class Platform(models.Model):
    """Платформа, на которой развёрнут клиент"""
    name = models.CharField(verbose_name="Название платформы", max_length=100, unique=True)
    description = models.TextField(verbose_name="Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Платформа"
        verbose_name_plural = "Платформы"
        db_table = "platform"

    def __str__(self):
        return self.name


class TechAccount(models.Model):
    """ Технические учетные записи """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tech_accounts", verbose_name="Клиент")
    username = models.CharField(verbose_name="Учетная запись", max_length=255)
    password = models.CharField(verbose_name="Пароль", max_length=255)
    description = models.CharField(verbose_name="Описание", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Техническая учётная запись"
        verbose_name_plural = "Технические учётные записи"
        db_table = "tech_account"

    def __str__(self):
        return f"{self.description} ({self.username})"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class TechNote(models.Model):
    """ Технические заметки клиента """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tech_notes", verbose_name="Клиент")
    note = models.TextField(verbose_name="Заметка")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Техническая заметка"
        verbose_name_plural = "Технические заметки"
        db_table = "tech_note"

    def __str__(self):
        return f"{self.client.client_name} - {self.created_at}"


class RemoteAccess(models.Model):
    """ Информация о подключении к клиенту """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="remote_access", verbose_name="Клиент")
    connection_details = models.TextField(verbose_name="Описание подключения")
    file_path = models.FileField(upload_to="remote_access/", blank=True, verbose_name="Файл-инструкция")

    class Meta:
        verbose_name = "Удалённый доступ"
        verbose_name_plural = "Информация о подключении"
        db_table = "remote_access"

    def __str__(self):
        return f"{self.client.client_name} - Доступ"


class ServerAccess(models.Model):
    """ Общие учетные записи для всех серверов клиента """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="server_accesses", verbose_name="Клиент")
    username = models.CharField(verbose_name="Имя пользователя", max_length=255)
    password = models.CharField(verbose_name="Пароль", max_length=255)
    description = models.CharField(verbose_name="Описание", max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Общая учётная запись"
        verbose_name_plural = "Общие учётные записи"
        db_table = "server_access"
        unique_together = ("client", "username")

    def __str__(self):
        return f"{self.client.client_name} - {self.username}"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
