from django.core.management.base import BaseCommand
from scripts.email.test_email import send_test_email

class Command(BaseCommand):
    help = 'Отправка тестового письма для проверки'

    def handle(self, *args, **kwargs):
        self.stdout.write("Запуск процесса отправки тестового письма...")
        result = send_test_email()
        if result is None:  # Успешная отправка
            self.stdout.write(self.style.SUCCESS('Тестовое письмо успешно отправлено'))
        else:
            self.stdout.write(self.style.ERROR(f'Ошибка отправки: {result}'))
