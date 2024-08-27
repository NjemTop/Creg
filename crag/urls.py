from django.contrib import admin
from .views import healthz, healthz_worker
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n"), name="set_language"),
    path('healthz/', healthz, name='health_check'),
    path('healthz_worker/', healthz_worker, name='health_check_worker'),
    path('', include('main.urls')),
    path('api/', include('api.urls')),
    path('apiv2/', include('apiv2.urls')),
    path('internal/', include('internal.urls'))
]
