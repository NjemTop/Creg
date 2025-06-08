from django.db import models

class OIDCSettings(models.Model):
    """Настройки OpenID Connect (OIDC) для Keycloak."""
    
    enabled = models.BooleanField("Включено", default=False)  # Флаг включения
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

    enabled = models.BooleanField("Включено", default=False)  # Флаг включения
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
