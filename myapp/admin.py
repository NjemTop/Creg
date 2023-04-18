from django.contrib import admin
from .models import BMInfoOnClient, ClientsCard, Favicon

admin.site.register(BMInfoOnClient)
admin.site.register(ClientsCard)

@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    fields = ['file']
