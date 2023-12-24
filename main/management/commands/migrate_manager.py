from django.core.management.base import BaseCommand
from main.models import ServiseCard, UsersBoardMaps

class Command(BaseCommand):
    help = 'Миграция данных менеджеров в таблице ServiceCard'

    def transliterate_name(self, name):
        # Словарь для транслитерации
        transliteration_dict = {
            'Ekaterina Shneyder': 'Екатерина Шнейдер',
            'Tatiana Shindikova': 'Татьяна Шиндикова',
        }
        return transliteration_dict.get(name, name)  # Возвращает транслитерированное имя, если оно есть в словаре

    def handle(self, *args, **kwargs):
        for service_card in ServiseCard.objects.all():
            manager_name = service_card.manager
            # Транслитерация имени
            manager_name_transliterated = self.transliterate_name(manager_name)
            self.stdout.write(self.style.SUCCESS(f'Обрабатывается ServiceCard: {service_card.id} менеджер {manager_name_transliterated}'))
            try:
                manager_obj = UsersBoardMaps.objects.get(name=manager_name_transliterated)
                service_card.manager_new = manager_obj
                service_card.save()
                self.stdout.write(self.style.SUCCESS(f'Менеджер {manager_name_transliterated} успешно мигрирован в таблице ServiceCard {service_card.id}'))
            except UsersBoardMaps.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Менеджер {manager_name_transliterated} не найден в таблице ServiceCard {service_card.id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Произошла ошибка: {e}"))
