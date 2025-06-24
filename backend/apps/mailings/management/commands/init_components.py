from django.core.management.base import BaseCommand
from apps.mailings.models import Component


class Command(BaseCommand):
    help = "Инициализирует компоненты рассылки"

    def handle(self, *args, **kwargs):
        Component.initialize_components()
        self.stdout.write(self.style.SUCCESS("Компоненты успешно созданы."))
