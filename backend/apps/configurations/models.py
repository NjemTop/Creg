from django.db import models


class OIDCSettings(models.Model):
    """Настройки OpenID Connect (OIDC) для Keycloak."""

    enabled = models.BooleanField("Включено", default=False)
    keycloak_base_url = models.URLField("Keycloak URL", default="https://keycloak.example.com/auth/")
    realm = models.CharField("Realm", max_length=100, default="realm")
    client_id = models.CharField("Client ID", max_length=255, default="client-id")
    client_secret = models.CharField("Client Secret", max_length=255, default="client-secret")

    def __str__(self):
        return f"OIDC: {self.realm} ({'Включено' if self.enabled else 'Отключено'})"

    class Meta:
        verbose_name = "OIDC Настройки"
        verbose_name_plural = "OIDC Настройки"


class SMTPSettings(models.Model):
    """Настройки SMTP для отправки почты"""

    enabled = models.BooleanField("Включено", default=False)
    smtp_host = models.CharField("SMTP сервер", max_length=255, default="smtp.example.com")
    smtp_port = models.IntegerField("SMTP порт", default=587)
    smtp_user = models.CharField("SMTP пользователь", max_length=255, blank=True, null=True)
    smtp_password = models.CharField("SMTP пароль", max_length=255, blank=True, null=True)
    use_tls = models.BooleanField("Использовать TLS", default=True)
    use_ssl = models.BooleanField("Использовать SSL", default=False)

    def __str__(self):
        return f"SMTP: {self.smtp_host}:{self.smtp_port} ({'Включено' if self.enabled else 'Отключено'})"

    class Meta:
        verbose_name = "SMTP Настройки"
        verbose_name_plural = "SMTP Настройки"


class IntegrationSettings(models.Model):
    """Настройки интеграций (Яндекс.Диск, Nextcloud и т.д.)"""

    # Yandex Disk
    yandex_token = models.CharField("OAuth-токен", max_length=255, blank=True)
    yandex_client_id = models.CharField("Yandex Client ID", max_length=255, blank=True)
    yandex_client_secret = models.CharField("Yandex Client Secret", max_length=255, blank=True)
    yandex_disk_folders = models.JSONField("Пути Яндекс.Диска", default=dict, blank=True)

    # Nextcloud
    nextcloud_url = models.URLField("Nextcloud URL", blank=True)
    nextcloud_user = models.CharField("Nextcloud пользователь", max_length=255, blank=True)
    nextcloud_password = models.CharField("Nextcloud пароль", max_length=255, blank=True)

    # SMB/File share
    file_share_username = models.CharField("SMB пользователь", max_length=255, blank=True)
    file_share_password = models.CharField("SMB пароль", max_length=255, blank=True)
    file_share_domain = models.CharField("SMB домен", max_length=255, blank=True)
    file_share_server = models.CharField("SMB сервер", max_length=255, blank=True)

    # Confluence credentials
    confluence_username = models.CharField("Confluence пользователь", max_length=255, blank=True)
    confluence_password = models.CharField("Confluence пароль", max_length=255, blank=True)

    # Telegram settings
    telegram_proxy = models.CharField("Telegram прокси", max_length=255, blank=True)
    telegram_bot_id = models.CharField("Telegram Bot ID", max_length=255, blank=True)
    telegram_bot_token = models.CharField("Telegram Bot Token", max_length=255, blank=True)

    # TFS settings
    tfs_assigned_to_product = models.CharField("TFS Assigned To", max_length=255, blank=True)

    # Ticket system settings
    ticket_api_endpoint = models.URLField("Ticket API Endpoint", blank=True)
    ticket_api_key = models.CharField("Ticket API Key", max_length=255, blank=True)
    ticket_api_secret = models.CharField("Ticket API Secret", max_length=255, blank=True)

    # Alert groups
    alert_group_support_team = models.CharField("Группа поддержки", max_length=255, blank=True)
    alert_group_release = models.CharField("Группа релизов", max_length=255, blank=True)
    alert_group_tickets = models.CharField("Группа тикетов", max_length=255, blank=True)

    # Yandex Disk for BMs Team
    yandex_dbs_token = models.CharField("Yandex DBS OAuth-токен", max_length=255, blank=True)
    yandex_dbs_client_id = models.CharField("Yandex DBS Client ID", max_length=255, blank=True)
    yandex_dbs_client_secret = models.CharField("Yandex DBS Client Secret", max_length=255, blank=True)

    def __str__(self):
        return "Integration settings"

    class Meta:
        verbose_name = "Интеграционные настройки"
        verbose_name_plural = "Интеграционные настройки"

