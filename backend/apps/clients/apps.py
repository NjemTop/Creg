from django.apps import AppConfig


class СlientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clients'

    def ready(self):
        import apps.clients.signals
