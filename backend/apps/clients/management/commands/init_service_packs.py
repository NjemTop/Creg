from django.core.management.base import BaseCommand
from apps.clients.models import ServicePack

class Command(BaseCommand):
    help = "Инициализирует тарифные планы"

    def handle(self, *args, **options):
        ServicePack.initialize_default_packs()
        self.stdout.write(self.style.SUCCESS("Тарифные планы успешно инициализированы."))
