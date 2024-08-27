from datetime import timedelta
from django.core.management.base import BaseCommand
from main.models import SLAPolicy

class Command(BaseCommand):
    help = 'Populate the SLAPolicy table with initial data'

    def handle(self, *args, **kwargs):
        data = [
            # (priority, plan, reaction_time, planned_resolution_time, max_resolution_time)
            ('critical', 'platinum', timedelta(minutes=15), timedelta(hours=2), timedelta(days=3)),
            ('critical', 'gold', timedelta(hours=1), timedelta(hours=6), timedelta(days=3)),
            ('critical', 'silver', timedelta(hours=3), timedelta(days=1), timedelta(days=4)),
            ('critical', 'bronze', timedelta(days=1), timedelta(days=3), timedelta(days=5)),
            ('high', 'platinum', timedelta(minutes=30), timedelta(hours=6), timedelta(days=3)),
            ('high', 'gold', timedelta(hours=3), timedelta(days=1), timedelta(days=4)),
            ('high', 'silver', timedelta(hours=5), timedelta(days=2), timedelta(days=5)),
            ('high', 'bronze', timedelta(days=2), timedelta(days=6), timedelta(days=10)),
            ('medium', 'platinum', timedelta(hours=3), timedelta(days=1), timedelta(days=4)),
            ('medium', 'gold', timedelta(hours=5), timedelta(days=2), timedelta(days=5)),
            ('medium', 'silver', timedelta(days=1), timedelta(days=5), timedelta(days=10)),
            ('medium', 'bronze', timedelta(days=2), timedelta(days=10), timedelta(days=30)),
            ('low', 'platinum', timedelta(hours=6), timedelta(days=2), timedelta(days=6)),
            ('low', 'gold', timedelta(days=1), timedelta(days=5), timedelta(days=10)),
            ('low', 'silver', timedelta(days=2), timedelta(days=7), timedelta(days=30)),
            ('low', 'bronze', timedelta(days=3), timedelta(days=10), timedelta(days=45)),
        ]
        
        for priority, plan, reaction_time, planned_resolution_time, max_resolution_time in data:
            SLAPolicy.objects.create(
                priority=priority,
                plan=plan,
                reaction_time=reaction_time,
                planned_resolution_time=planned_resolution_time,
                max_resolution_time=max_resolution_time
            )
        self.stdout.write(self.style.SUCCESS('Successfully populated the SLAPolicy table'))
