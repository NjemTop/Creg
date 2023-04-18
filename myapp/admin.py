from django.contrib import admin
from .models import BMInfoOnClient, ClientsCard, ContactsCard, Favicon

admin.site.register(BMInfoOnClient)
admin.site.register(ClientsCard)
admin.site.register(ContactsCard)

@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    fields = ['file']
