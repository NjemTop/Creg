from django.contrib import admin
from .models import BMInfoOnClient, Favicon

admin.site.register(BMInfoOnClient)

@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    fields = ['file']
