from django.contrib import admin
from django.conf import settings

admin.site.site_header = f"Администрирование Creg (version {settings.VERSION})"
