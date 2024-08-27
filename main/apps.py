from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.signals
        from django.contrib import admin
        from crag.version import __version__
        admin.site.site_header = f'version {__version__}'
        admin.site.site_title = 'Creg'
        admin.site.index_title = 'Админ-панель'
