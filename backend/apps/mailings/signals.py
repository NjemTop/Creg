from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Component


@receiver(post_migrate)
def create_default_components(sender, **kwargs):
    """Создаёт стандартные компоненты после миграции"""
    if sender.name == "apps.mailings":
        Component.initialize_components()
