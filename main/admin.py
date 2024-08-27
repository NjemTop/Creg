from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ClientsList, ReportTicket, Secret, SLAPolicy, ReportDownloadjFrog, UsersBoardMaps, ClientsCard, 
    ContactsCard, ConnectInfoCard, BMServersCard, Integration, ModuleCard, 
    TechAccountCard, ConnectionInfo, ServiseCard, TechInformationCard, TechNote, 
    ReleaseInfo, Favicon, TaskExecution, ClientSyncStatus)
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
from django.contrib.admin.models import LogEntry
from api.tasks import update_module_info_task
from main.tasks import add_user_jfrog_task, update_tickets


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


@admin.register(Secret)
class SecretAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('name',)


# Example used!!!
def get_secret_value(name):
    try:
        secret = Secret.objects.get(name=name)
        return secret.value
    except Secret.DoesNotExist:
        return None


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
    list_display = ('id', 'client_name', 'contact_name', 'firstname', 'lastname', 'contact_position', 'contact_email', 'contact_number', 'notification_update', 'contact_notes', 'last_updated')
    list_display_links = ('contact_email',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

class ServiseCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'service_pack', 'manager', 'loyal',  'last_updated')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

class ClientsListAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'short_name', 'password', 'contact_status', 'last_updated')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'

class TechInformationCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'server_version', 'update_date',  'last_updated')
    list_display_links = ('client_name',)

    def client_name(self, obj):
        return obj.client_card.client_info.client_name
    client_name.short_description = 'Клиент'


class UsersBoardMapsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'position',  'agent_id', 'test_automatic_email', 'new_client')
    list_display_links = ('name',)


class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ('priority', 'plan', 'formatted_reaction_time', 'formatted_planned_resolution_time', 'formatted_max_resolution_time')

# Создаем пользовательскую модель для отображения в админ-панели
class AdminLogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'decoded_change_message')
    search_fields = ('user__username', 'object_repr', 'change_message')
    date_hierarchy = 'action_time'

    def decoded_change_message(self, obj):
        # Декодируем сообщение, если оно не пустое
        if obj.change_message and obj.change_message.startswith('['):
            try:
                decoded_message = json.loads(obj.change_message)
                readable_messages = []
                for change in decoded_message:
                    if 'fields' in change.get('changed', {}):
                        fields = change['changed']['fields']
                        readable_fields = ', '.join(fields)
                        readable_messages.append(f"Измененные поля: {readable_fields}")
                return format_html('<br>'.join(readable_messages))
            except json.JSONDecodeError:
                return obj.change_message
        return obj.change_message

    decoded_change_message.short_description = 'Изменения'

# Регистрируем модель LogEntry для отображения в админ-панели
admin.site.register(LogEntry, AdminLogEntryAdmin)

admin.site.register(ClientsList, ClientsListAdmin)
admin.site.register(ClientsCard, ClientsCardAdmin)
admin.site.register(ContactsCard, ContactsCardAdmin)
admin.site.register(ConnectInfoCard)
admin.site.register(BMServersCard)
admin.site.register(Integration)
admin.site.register(ModuleCard)
admin.site.register(TechAccountCard)
admin.site.register(ServiseCard, ServiseCardAdmin)
admin.site.register(TechInformationCard, TechInformationCardAdmin)
admin.site.register(TechNote)
admin.site.register(ReleaseInfo)
admin.site.register(ReportTicket)
admin.site.register(SLAPolicy, SLAPolicyAdmin)
admin.site.register(ReportDownloadjFrog)
admin.site.register(UsersBoardMaps, UsersBoardMapsAdmin)
admin.site.register(ClientSyncStatus)
admin.site.register(TaskExecution)


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
