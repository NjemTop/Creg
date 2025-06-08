from django.contrib import admin
from apps.clients.models import (
    Language, Client, Contact, ServiceInfo, TechnicalInfo, ServerVersionHistory,
    Module, ClientModule, Integration, ClientIntegration, 
    Server, ServerRole, TechAccount, TechNote, RemoteAccess, ServerAccess
)


# 🔹 Inline-админки для связанных моделей
class ContactInline(admin.TabularInline):
    model = Contact
    extra = 1


class ClientModuleInline(admin.TabularInline):
    model = ClientModule
    extra = 1


class ClientIntegrationInline(admin.TabularInline):
    model = ClientIntegration
    extra = 1


class ServerInline(admin.TabularInline):
    model = Server
    extra = 1


class TechAccountInline(admin.TabularInline):
    model = TechAccount
    extra = 1


class ServerAccessInline(admin.TabularInline):
    model = ServerAccess
    extra = 1


class RemoteAccessInline(admin.TabularInline):
    model = RemoteAccess
    extra = 1


class TechNoteInline(admin.TabularInline):
    model = TechNote
    extra = 1


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ["name"]


# Клиенты
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("client_name", "short_name", "contact_status", "saas", "language", "created_at", "updated_at")
    list_filter = ("contact_status", "saas", "language__name", "created_at")
    search_fields = ("client_name", "short_name", "language__name")
    ordering = ["client_name"]

    inlines = [
        ContactInline, ClientModuleInline, ClientIntegrationInline,
        ServerInline, TechAccountInline, ServerAccessInline,
        RemoteAccessInline, TechNoteInline
    ]

# Контакты
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "client", "email", "position", "phone_number", "notification_update", "updated_at")
    list_filter = ("notification_update", "client")
    search_fields = ("first_name", "last_name", "email")
    ordering = ["last_name", "first_name"]

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "ФИО"


# Обслуживание клиента
@admin.register(ServiceInfo)
class ServiceInfoAdmin(admin.ModelAdmin):
    list_display = ("client", "service_pack", "manager", "loyalty", "updated_at")
    list_filter = ("service_pack", "loyalty")
    search_fields = ("client__client_name", "manager__name")


# Техническая информация клиента
@admin.register(TechnicalInfo)
class TechnicalInfoAdmin(admin.ModelAdmin):
    list_display = ("client", "server_version", "update_date", "api_enabled", "mdm_support")
    list_filter = ("api_enabled", "mdm_support", "localized_web", "localized_ios", "skins_web", "skins_ios")
    search_fields = ("client__client_name", "server_version")
    readonly_fields = ("previous_version", "previous_update_date")


# История обновлений серверов
@admin.register(ServerVersionHistory)
class ServerVersionHistoryAdmin(admin.ModelAdmin):
    list_display = ("client", "version", "update_date")
    list_filter = ("update_date",)
    search_fields = ("client__client_name", "version")


# Модули и связи
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(ClientModule)
class ClientModuleAdmin(admin.ModelAdmin):
    list_display = ("client", "module", "is_active", "added_at")
    list_filter = ("is_active",)
    search_fields = ("client__client_name", "module__name")


# Интеграции и связи
@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(ClientIntegration)
class ClientIntegrationAdmin(admin.ModelAdmin):
    list_display = ("client", "integration", "is_active", "added_at")
    list_filter = ("is_active",)
    search_fields = ("client__client_name", "integration__name")


# Серверы и роли серверов
@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("client", "name", "ip_address", "role", "operating_system", "updated_at")
    list_filter = ("role", "client")
    search_fields = ("name", "ip_address", "client__client_name")
    ordering = ["client__client_name", "name"]


@admin.register(ServerRole)
class ServerRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


# Учётные записи (тех. и серверные)
@admin.register(TechAccount)
class TechAccountAdmin(admin.ModelAdmin):
    list_display = ("client", "username", "description", "updated_at")
    search_fields = ("username", "client__client_name")
    ordering = ["client__client_name"]


@admin.register(ServerAccess)
class ServerAccessAdmin(admin.ModelAdmin):
    list_display = ("client", "username", "description", "updated_at")
    search_fields = ("username", "client__client_name")
    ordering = ["client__client_name"]


# Удалённый доступ и заметки
@admin.register(RemoteAccess)
class RemoteAccessAdmin(admin.ModelAdmin):
    list_display = ("client", "connection_details", "file_path")
    search_fields = ("client__client_name", "connection_details")


@admin.register(TechNote)
class TechNoteAdmin(admin.ModelAdmin):
    list_display = ("client", "note", "created_at")
    search_fields = ("client__client_name", "note")
