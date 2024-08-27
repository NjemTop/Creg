from datetime import timedelta
from django.core.management.base import BaseCommand
from main.models import ReportTicket

class Command(BaseCommand):
    help = 'Конвертирует временные поля из IntegerField в DurationField'

    def handle(self, *args, **options):
        tickets = ReportTicket.objects.all()
        for ticket in tickets:
            if ticket.first_response_time is not None:
                ticket.first_response_time_temp = timedelta(minutes=ticket.first_response_time)
            if ticket.sla_time is not None:
                ticket.sla_time_temp = timedelta(minutes=ticket.sla_time)
            ticket.save()
        self.stdout.write(self.style.SUCCESS('Успешно конвертированы временные поля для всех заявок'))
