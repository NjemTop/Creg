from django.core.management.base import BaseCommand
from apps.clients.models import Language


class Command(BaseCommand):
    help = "Инициализирует стандартные языки"

    def handle(self, *args, **options):
        Language.initialize_languages()
        self.stdout.write(self.style.SUCCESS("Языки успешно инициализированы."))
