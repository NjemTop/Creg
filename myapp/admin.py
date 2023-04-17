from django.contrib import admin
from .models import Client, Favicon

admin.site.register(Client)

@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    pass