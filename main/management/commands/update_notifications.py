from django.core.management.base import BaseCommand
from main.models import ContactsCard

class Command(BaseCommand):
    help = 'Переносит данные из notification_update в notification_update_new'

    def handle(self, *args, **kwargs):
        self.stdout.write("Запуск процесса обновления...")
        contacts = ContactsCard.objects.all()

        for contact in contacts:
            # Проверяем содержание поля notification_update
            if contact.notification_update in ["Основной", "Копия"]:
                contact.notification_update_new = True
            else:
                # Если поле пустое или содержит "Нет рассылки", оставляем False
                contact.notification_update_new = False
            # Сохраняем изменения в базе данных
            contact.save()

        self.stdout.write(self.style.SUCCESS('Успешно обновлено %s контактов' % len(contacts)))
