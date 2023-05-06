from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from . import views

schema_view = get_schema_view(
   openapi.Info(
      title="REST API",
      default_version='v1',
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
    path('clients', views.clients, name='clients'),
    path('create_client', views.create_client, name='create'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)