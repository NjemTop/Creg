from django.core.management.base import BaseCommand
from django.core.files import File
from main.models import DatabaseBackup
import os

class Command(BaseCommand):
    help = 'Сканирует каталог резервных копий и добавляет новые резервные копии в базу данных.'

    def handle(self, *args, **kwargs):
        backup_directory = 'backup/db/'  # Путь к папке с бэкапами
        existing_backups = set(DatabaseBackup.objects.values_list('file_name', flat=True))

        for filename in os.listdir(backup_directory):
            if filename.endswith('.psql.bin') and filename not in existing_backups:
                file_path = os.path.join(backup_directory, filename)

                # Создание нового объекта DatabaseBackup
                backup = DatabaseBackup(file_name=filename)
                with open(file_path, 'rb') as file:
                    backup.file.save(filename, File(file), save=True)
                
                self.stdout.write(self.style.SUCCESS(f'Добавлен файл резервной копии {filename} в базу данных'))
