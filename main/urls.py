from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from . import views
from django.views.generic import TemplateView

schema_view = get_schema_view(
   openapi.Info(
      title="REST API",
      default_version='v2',
      description="Описание REST API",
      terms_of_service="/",
      contact=openapi.Contact(email="oleg.eliseev@boardmaps.ru"),
      # license=openapi.License(name="License"), 
   ),
   public=True,
   permission_classes=(AllowAny,),
)

urlpatterns = [
    path('', views.index, name='home'),
    path('accounts/login/', views.custom_login, name='custom_login'),
    path('blocked/', TemplateView.as_view(template_name='main/registration/blocked.html'), name='blocked'),
    path('run_command/', views.run_command, name='run_command'),
    path('clients/', views.clients, name='clients'),
    path('client/<int:client_id>/', views.client, name='client'),
    path('document_preview/<path:file_path>/', views.document_preview, name='document_preview'),
    path('client/<int:client_id>/add_contact/', views.add_contact, name='add_contact'),
    path('create_client/', views.create_client, name='create_client'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('release_info/', views.release_info, name='release_info'),
    path('get_contacts/<int:client_id>/', views.get_contacts, name='get_contacts'),
    path('update_integration/<int:client_id>/', views.update_integration, name='update_integration'),
    path('search_results/', views.search_results, name='search_results'),
    path('search_versions/', views.search_versions, name='search_versions'),
    path('report/', views.report, name='report'),
    path('mailing/', views.mailing, name='mailing'),
    path('report_tickets/', views.report_tickets, name='report_tickets'),
    path('get_report_data/', views.get_report_data, name='get_report_data'),
    path('report_jfrog/', views.report_jfrog, name='report_jfrog'),
    path('api2/get_report_jfrog/', views.get_report_jfrog, name='get_report_jfrog'),
    path('api2/get_unique_accounts/', views.get_unique_accounts, name='get_unique_accounts'),
    path('api2/get_unique_versions/', views.get_unique_versions, name='get_unique_versions'),
    path('add_user_nextcloud/', views.add_user_nextcloud, name='add_user_nextcloud'),
    path('delete_user_nextcloud/', views.delete_user_nextcloud, name='delete_user_nextcloud'),
    path('update_tickets/', views.update_tickets_view, name='update_tickets'),
    path('test/', views.test, name='test'),
    path('obfuscate_mssql/', views.obfuscate_mssql, name='obfuscate_mssql'),
    path('obfuscate_postgresql/', views.obfuscate_postgresql, name='obfuscate_postgresql'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
