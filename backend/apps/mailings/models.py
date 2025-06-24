from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from apps.clients.models import Module


User = get_user_model()


class MailingMode(models.TextChoices):
    TEST = 'test', 'Тестовая'
    PROD = 'prod', 'Продакшен'


class ReleaseType(models.TextChoices):
    RELEASE_2X = 'release2x', '2.0'
    RELEASE_3X = 'release3x', '3.0'


class MailingStatus(models.TextChoices):
    DRAFT = 'draft', _("Черновик")
    PENDING = 'pending', _("Ожидание")
    IN_PROGRESS = 'in_progress', _("В процессе")
    COMPLETED = 'completed', _("Завершено")
    FAILED = 'failed', _("Ошибка")

    @classmethod
    def get_display(cls, status_code):
        """Возвращает локализованное название статуса"""
        return str(dict(cls.choices).get(status_code, status_code))


class RecipientStatus(models.TextChoices):
    PENDING = 'pending', 'Ожидание'
    SENT = 'sent', 'Отправлено'
    ERROR = 'error', 'Ошибка'

class LogLevel(models.TextChoices):
    """Уровни логирования"""
    INFO = "info", "INFO"
    WARNING = "warning", "WARNING"
    ERROR = "error", "ERROR"
    CRITICAL = "critical", "CRITICAL"


class Component(models.Model):
    """Модель компонентов рассылки (Server, iPad, Android)"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Код компонента")
    name = models.CharField(max_length=50, verbose_name="Название компонента")

    class Meta:
        verbose_name = "Компонент"
        verbose_name_plural = "Компоненты"
        db_table = "component"

    def __str__(self):
        return self.name

    @staticmethod
    def initialize_components():
        """Автоматическое заполнение таблицы `Component` стандартными значениями"""
        defaults = [
            {"code": "server", "name": "Server"},
            {"code": "ipad", "name": "iPad"},
            {"code": "android", "name": "Android"},
        ]
        for comp in defaults:
            Component.objects.get_or_create(code=comp["code"], defaults={"name": comp["name"]})


class Mailing(models.Model):
    """Таблица с информацией о рассылке клиенту"""

    mode = models.CharField(
        max_length=10,
        choices=MailingMode.choices, 
        default=MailingMode.PROD, 
        verbose_name="Режим"
    )

    release_type = models.CharField(
        max_length=50,
        choices=ReleaseType.choices, 
        default=ReleaseType.RELEASE_3X, 
        verbose_name="Версия релиза"
    )

    components = models.ManyToManyField(
        Component,
        related_name="mailings",
        verbose_name="Компоненты"
    )

    server_version = models.CharField(max_length=20, blank=True, verbose_name="Версия server")
    ipad_version = models.CharField(max_length=20, blank=True, verbose_name="Версия iPad")
    android_version = models.CharField(max_length=20, blank=True, verbose_name="Версия Android")

    service_window = models.BooleanField(default=False, verbose_name="Запрос сервисного окна")
    saas_notification = models.BooleanField(default=False, verbose_name="Отправить уведомление в SaaS")
    saas_update_time = models.DateTimeField(blank=True, null=True, verbose_name="Время обновления SaaS")
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Модуль")

    status = models.CharField(max_length=20, choices=MailingStatus.choices, default=MailingStatus.PENDING, verbose_name="Статус")
    language = models.ForeignKey('clients.Language', on_delete=models.SET_NULL, verbose_name="Язык рассылки", blank=True, null=True)

    started_at = models.DateTimeField(blank=True, null=True, verbose_name="Начало отправки")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Завершение отправки")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Создал")

    error_message = models.TextField(blank=True, null=True, verbose_name="Ошибка")

    def release_number(self):
        """Автоматически формирует номер релиза"""
        versions = []
        if self.server_version:
            versions.append(f"Server {self.server_version}")
        if self.ipad_version:
            versions.append(f"iPad {self.ipad_version}")
        if self.android_version:
            versions.append(f"Android {self.android_version}")

        return ", ".join(versions) if versions else "Нет компонентов"

    def primary_component(self):
        """Определяет основной компонент рассылки"""
        if self.server_version:
            return "Server"
        elif self.ipad_version:
            return "iPad"
        elif self.android_version:
            return "Android"
        return "Не определён"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        db_table = "mailing"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        return self.release_number()


class MailingRecipient(models.Model):
    """Клиенты, которым отправляется рассылка (продакшен)"""
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='recipients')
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, verbose_name="Клиент")
    email = models.EmailField(verbose_name="Почта клиента")
    status = models.CharField(max_length=20, choices=RecipientStatus.choices, default=RecipientStatus.PENDING, verbose_name="Статус отправки")
    error_message = models.TextField(blank=True, null=True, verbose_name="Ошибка")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Время отправки")

    def __str__(self):
        return f"{self.client.client_name} -> {self.email} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        db_table = "mailing_recipient"

class MailingTestRecipient(models.Model):
    """Тестовые отправки"""
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='test_recipients')
    email = models.EmailField(verbose_name="Тестовый email")
    status = models.CharField(max_length=20, choices=RecipientStatus.choices, default=RecipientStatus.PENDING, verbose_name="Статус отправки")
    error_message = models.TextField(blank=True, null=True, verbose_name="Ошибка")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Время отправки")

    class Meta:
        verbose_name = "Тестовый получатель"
        verbose_name_plural = "Тестовые получатели"
        db_table = "mailing_test_recipient"

    def __str__(self):
        return f"Тестовая отправка -> {self.email} ({self.get_status_display()})"


class MailingLog(models.Model):
    """Логи работы рассылок"""
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="logs", verbose_name="Рассылка")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")
    level = models.CharField(max_length=10, choices=LogLevel.choices, default=LogLevel.INFO, verbose_name="Уровень")
    message = models.TextField(verbose_name="Сообщение")

    class Meta:
        verbose_name = "Лог рассылки"
        verbose_name_plural = "Логи рассылок"
        db_table = "mailing_log"
        indexes = [
            models.Index(fields=["mailing", "timestamp"]),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.get_level_display()} - {self.message[:50]}"
