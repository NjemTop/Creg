from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ClientsList, ReportTicket, ReportDownloadjFrog, UsersBoardMaps, ClientsCard, 
    ContactsCard, ConnectInfoCard, BMServersCard, Integration, ModuleCard, 
    TechAccountCard, ConnectionInfo, ServiseCard, TechInformationCard, TechNote, 
    ReleaseInfo, Favicon)
from .models import backup_file_path, DatabaseBackup
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.core.management import call_command
from django.db import DatabaseError
from django.contrib import messages
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.files import File
from io import StringIO
import json
import os
import logging
from django_celery_beat.models import PeriodicTask
from api.tasks import add_user_jfrog_task, update_module_info_task, update_tickets


logger = logging.getLogger(__name__)

@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    change_list_template = 'admin/db_backup_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backup/', self.admin_site.admin_view(self.make_backup), name='backup'),
            path('restore/', self.admin_site.admin_view(self.restore_backup), name='restore'),
            path('restore/<int:backup_id>/', self.admin_site.admin_view(self.restore_backup_selected), name='restore-selected'),
        ]
        return custom_urls + urls

    def make_backup(self, request):
        # Выполнение команды dbbackup для создания бэкапа
        call_command('dbbackup')

        # Поиск последнего созданного файла бэкапа
        backup_files = [f for f in os.listdir('backup/db/') if f.endswith('.psql.bin')]
        backup_files.sort(reverse=True)
        if not backup_files:
            self.message_user(request, 'Ошибка создания бэкапа', level=messages.ERROR)
            logger.error(f'Ошибка создания бэкапа')
            return redirect('..')

        latest_backup_file = backup_files[0]

        # Проверка, зарегистрирован ли уже этот файл в базе данных
        if not DatabaseBackup.objects.filter(file_name=latest_backup_file).exists():
            file_path = os.path.join('backup/db/', latest_backup_file)

            # Создание записи в базе данных
            backup = DatabaseBackup(file_name=latest_backup_file)
            backup.file.name = file_path
            backup.save()
            self.message_user(request, 'Бэкап успешно выполнен')
            logger.info(f'Бэкап успешно выполнен')
        else:
            self.message_user(request, 'Файл бэкапа уже существует', level=messages.INFO)
            logger.error(f'Файл бэкапа уже существует')

        return redirect('..')

    def restore_backup(self, request):
        backups = DatabaseBackup.objects.all()
        context = {
            'backups': backups,
        }
        return render(request, 'admin/restore_backup.html', context)

    def restore_backup_selected(self, request, backup_id):
        try:
            backup = DatabaseBackup.objects.get(id=backup_id)
            call_command('dbrestore', '--noinput')
            self.message_user(request, 'Бэкап успешно восстановлен')
            logger.info(f'Бэкап успешно восстановлен')
        except DatabaseError:
            self.message_user(request, 'Ошибка при восстановлении бэкапа', level=messages.ERROR)
            logger.error(f'Ошибка при восстановлении бэкапа')
        except DatabaseBackup.DoesNotExist:
            self.message_user(request, 'Выбранного бэкапа не существует', level=messages.ERROR)
            logger.error(f'Выбранного бэкапа не существует')
        return redirect('..')


def run_selected_tasks(modeladmin, request, queryset):
    for task in queryset:
        args = json.loads(task.args)  # Десериализация аргументов из JSON
        if task.task == 'api.tasks.add_user_jfrog_task':
            add_user_jfrog_task.delay(*args)  # Используйте delay() для запуска задачи
        elif task.task == 'api.tasks.update_module_info_task':
            update_module_info_task.delay(*args)  # Используйте delay() для запуска задачи
        elif task.task == 'api.tasks.update_tickets':
            update_tickets.delay(*args)  # Используем метод delay() для запуска задачи
        task.last_run_at = timezone.now()  # Установка времени последнего запуска
        task.save()

run_selected_tasks.short_description = "Запустить выбранные задачи"

class PeriodicTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'task', 'enabled')
    actions = [run_selected_tasks]

# Повторная регистрация модели PeriodicTask
admin.site.register(PeriodicTask, PeriodicTaskAdmin)

# Отмена регистрации модели PeriodicTask
admin.site.unregister(PeriodicTask)

class ClientsCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'contacts', 'tech_notes', 'connect_info', 'rdp', 'tech_account', 'bm_servers')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_info.client_name
    client_name.short_description = 'Клиент'


class ContactsCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'contact_name', 'contact_position', 'contact_email', 'notification_update', 'contact_notes')
    list_display_links = ('contact_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

class ServiseCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'service_pack', 'manager', 'loyal')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

class ClientsListAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'short_name', 'password', 'contact_status')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'


admin.site.register(ClientsList, ClientsListAdmin)
admin.site.register(ClientsCard, ClientsCardAdmin)
admin.site.register(ContactsCard, ContactsCardAdmin)
admin.site.register(ConnectInfoCard)
admin.site.register(BMServersCard)
admin.site.register(Integration)
admin.site.register(ModuleCard)
admin.site.register(TechAccountCard)
admin.site.register(ServiseCard, ServiseCardAdmin)
admin.site.register(TechInformationCard)
admin.site.register(TechNote)
admin.site.register(ReleaseInfo)
admin.site.register(ReportTicket)
admin.site.register(ReportDownloadjFrog)
admin.site.register(UsersBoardMaps)


@admin.register(Favicon)
class FaviconAdmin(admin.ModelAdmin):
    fields = ['file']


@admin.register(ConnectionInfo)
class ConnectionInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'file_link', 'text')
    list_display_links = ('id', 'client_name', 'file_link', 'text')

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

    def file_link(self, obj):
        if obj.file_path and hasattr(obj.file_path, 'url'):
            return format_html('<a href="{}">{}</a>', obj.file_path.url, obj.file_path.name)
        else:
            return "No file"
    file_link.short_description = 'Файл'
