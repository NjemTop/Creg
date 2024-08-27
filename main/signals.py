from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ClientsCard, Integration

@receiver(post_save, sender=ClientsCard)
def create_default_integration(sender, instance, created, **kwargs):
    if created:
        Integration.objects.create(client_card=instance)
