from django.contrib import admin
from django.utils.html import format_html
from .models import ClientsList, ReportTicket, ClientsCard, ContactsCard, ConnectInfoCard, BMServersCard, Integration, ModuleCard, TechAccountCard, ConnectionInfo, ServiseCard, TechInformationCard, TechNote, ReleaseInfo, Favicon
from .models import backup_file_path, DatabaseBackup
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.core.management import call_command
from django.db import DatabaseError
from django.contrib import messages
from datetime import datetime
from django.core.files.base import ContentFile
from io import StringIO


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
        output = StringIO()
        call_command('dbbackup', stdout=output)
        file_content = output.getvalue()
        output.close()

        # Возьмите имя файла из команды dbbackup и сохраните его в базе данных.
        # Например, вы можете использовать текущее время для создания имени файла.
        file_name = datetime.now().strftime("backup_%Y%m%d%H%M%S")
        file_path = backup_file_path(None, file_name)
        backup = DatabaseBackup(file_name=file_name)
        backup.file.save(file_path, ContentFile(file_content))
        backup.save()

        self.message_user(request, 'Бэкап успешно выполнен')
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
        except DatabaseError:
            self.message_user(request, 'Ошибка при восстановлении бэкапа', level=messages.ERROR)
        except DatabaseBackup.DoesNotExist:
            self.message_user(request, 'Выбранного бэкапа не существует', level=messages.ERROR)
        return redirect('..')


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


admin.site.register(ClientsList)
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
