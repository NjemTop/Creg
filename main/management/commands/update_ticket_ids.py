from django.core.management.base import BaseCommand
from main.models import ReportTicket

class Command(BaseCommand):
    help = 'Обновление id заявок с префиксом для сохранения уникальности в новой билетной системе'

    def handle(self, *args, **options):
        self.stdout.write("Запуск процесса обновления...")
        updated_count = 0
        for ticket in ReportTicket.objects.all():
            if ticket.ticket_id is not None and not str(ticket.ticket_id).startswith("HF_"):
                original_ticket_id = ticket.ticket_id
                ticket.ticket_id = f"HF_{ticket.ticket_id}"
                ticket.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Updated ticket ID from {original_ticket_id} to {ticket.ticket_id}"
                ))
        self.stdout.write(self.style.SUCCESS(
            f"Total tickets updated: {updated_count}"
        ))
