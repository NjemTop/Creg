from django.contrib import admin
from .models import ClientsList, ClientsCard, ContactsCard, ConnectInfoCard, BMServersCard, Favicon


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


admin.site.register(ClientsList)
admin.site.register(ClientsCard, ClientsCardAdmin)
admin.site.register(ContactsCard, ContactsCardAdmin)
admin.site.register(ConnectInfoCard)
admin.site.register(BMServersCard)

@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    fields = ['file']