from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from . import views

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
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('clients/', views.clients, name='clients'),
    path('client/<int:client_id>/', views.client, name='client'),
    path('client/<int:client_id>/add_contact/', views.add_contact, name='add_contact'),
    path('create_client/', views.create_client, name='create_client'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('release_info/', views.release_info, name='release_info'),
    path('get_contacts/<int:client_id>/', views.get_contacts, name='get_contacts'),
    path('update_integration/<int:client_id>/', views.update_integration, name='update_integration'),
    path('search_results/', views.search_results, name='search_results'),
    path('report/', views.report, name='report'),
    path('test_task/', views.test_task, name='test_task'),
    path('test_task/<str:task_id>/', views.get_task_info, name='test_task'),
    path('test_email_task/', views.test_send_email_task, name='test_email_task'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
