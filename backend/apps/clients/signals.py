from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Language


@receiver(post_migrate)
def create_default_languages(sender, **kwargs):
    """Создаёт стандартные языки после миграции"""
    if sender.name == "apps.clients":
        Language.initialize_languages()
