from django.contrib import admin
from django.utils.html import format_html
from .models import ClientsList, ClientsCard, ContactsCard, ConnectInfoCard, BMServersCard, Integration, TechAccountCard, ConnectionInfo, ServiseCard, TechInformationCard, TechNote, Favicon


class ClientsCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'contacts', 'tech_notes', 'connect_info', 'rdp', 'tech_account', 'bm_servers')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_info.client_name
    client_name.short_description = 'Клиент'


class ContactsCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'contact_name', 'contact_position', 'contact_email', 'notification_update', 'contact_notes')
    list_display_links = ('contact_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

class ServiseCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'service_pack', 'manager', 'loyal')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

admin.site.register(ClientsList)
admin.site.register(ClientsCard, ClientsCardAdmin)
admin.site.register(ContactsCard, ContactsCardAdmin)
admin.site.register(ConnectInfoCard)
admin.site.register(BMServersCard)
admin.site.register(Integration)
admin.site.register(TechAccountCard)
admin.site.register(ServiseCard, ServiseCardAdmin)
admin.site.register(TechInformationCard)
admin.site.register(TechNote)

@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    fields = ['file']

@admin.register(ConnectionInfo)
class ConnectionInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'file_link', 'text')
    list_display_links = ('id', 'client_name', 'file_link', 'text')

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

    def file_link(self, obj):
        return format_html('<a href="{}">{}</a>', obj.file_path.url, obj.file_path.name)
    file_link.short_description = 'Файл'
