from django.contrib import admin
from apps.mailings.models import Mailing, MailingLog, MailingRecipient, MailingTestRecipient, Component


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "release_number", "primary_component", "status", "created_at")
    list_filter = ("status", "created_at", "language")
    search_fields = ("id", "release_type", "server_version", "ipad_version", "android_version")
    filter_horizontal = ("components",)
    readonly_fields = ("release_number", "primary_component")


admin.site.register(MailingLog)
admin.site.register(MailingRecipient)
admin.site.register(MailingTestRecipient)
