from django.contrib import admin
from .models import OIDCSettings, SMTPSettings

@admin.register(OIDCSettings)
class OIDCSettingsAdmin(admin.ModelAdmin):
    list_display = ("keycloak_base_url", "realm", "client_id")

@admin.register(SMTPSettings)
class SMTPSettingsAdmin(admin.ModelAdmin):
    list_display = ("smtp_host", "smtp_port", "enabled", "use_tls", "use_ssl")
    list_editable = ("enabled", "use_tls", "use_ssl")

    def save_model(self, request, obj, form, change):
        """Отключаем все другие SMTP, если включается новый"""
        if obj.enabled:
            SMTPSettings.objects.exclude(id=obj.id).update(enabled=False)
        super().save_model(request, obj, form, change)
