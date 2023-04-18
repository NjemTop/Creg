from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import web_views
from . import api_views

urlpatterns = [
    path('', web_views.index, name='index'),
    path('get_clients/', web_views.get_clients, name='get_clients'),
    path('search/', web_views.search_clients, name='search_clients'),
    path('get_client/<int:client_id>/', web_views.get_client, name='get_client'),
    path('api/get_clients/', api_views.api_get_clients, name='api_get_clients'),
    path('api/add_client/', api_views.api_add_client, name='api_add_client'),
    path('add_client/', web_views.add_client, name='add_client'),
    path('add_client_web/', api_views.add_client_web, name='add_client_web')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)