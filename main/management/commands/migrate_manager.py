from django.core.management.base import BaseCommand
from main.models import ServiseCard, UsersBoardMaps

class Command(BaseCommand):
    help = 'Миграция данных менеджеров в таблице ServiseCard'

    def add_arguments(self, parser):
        self.stdout.write("Запуск процесса миграции менеджеров...")
        # Добавляем аргументы командной строки для ID старого и нового менеджера
        parser.add_argument('old_manager_id', type=int, help='ID старого менеджера')
        parser.add_argument('new_manager_id', type=int, help='ID нового менеджера')

    def handle(self, *args, **options):
        old_manager_id = options['old_manager_id']
        new_manager_id = options['new_manager_id']

        # Получаем объекты менеджеров
        try:
            old_manager = UsersBoardMaps.objects.get(id=old_manager_id)
            new_manager = UsersBoardMaps.objects.get(id=new_manager_id)
        except UsersBoardMaps.DoesNotExist as error_message:
            self.stdout.write(self.style.ERROR(f"Менеджер не найден: {error_message}"))
            return

        # Подсчет количества обновленных записей
        updated_count = 0

        for service_card in ServiseCard.objects.filter(manager=old_manager):
            service_card.manager = new_manager
            service_card.save()
            updated_count += 1
            self.stdout.write(self.style.SUCCESS(f'Менеджер {old_manager.name} ({service_card.client_card.client_info.client_name}) изменен на {new_manager.name}'))

        self.stdout.write(self.style.SUCCESS(f'Всего обновлено записей: {updated_count}'))
