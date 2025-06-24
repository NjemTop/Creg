from django.core.management.base import BaseCommand
from apps.clients.models import ServerRole, Platform

class Command(BaseCommand):
    help = "Инициализирует роли серверов и платформы"

    def handle(self, *args, **options):
        roles = ["master", "worker", "nfs", "oos", "r7-office", "db", "web"]
        platforms = ["K8s", "DeckHouse", "Windows Server"]

        for role in roles:
            ServerRole.objects.get_or_create(name=role)

        for plat in platforms:
            Platform.objects.get_or_create(name=plat)

        self.stdout.write(self.style.SUCCESS("Роли серверов и платформы успешно инициализированы."))
