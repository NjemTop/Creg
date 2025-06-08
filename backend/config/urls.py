"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path("api/", include("apps.api.urls")),
    path('clients/', include('apps.clients.urls')),
    path('mailings/', include('apps.mailings.urls')),
    path('reports/', include('apps.reports.urls')),
    path("auth/", include("apps.authentication.urls")),
    path("oidc/", include("mozilla_django_oidc.urls"), name="oidc"),
    path('internal/', include('apps.internal.urls')),
]

handler400 = "apps.core.views.custom_400"
handler404 = "apps.core.views.custom_404"
handler500 = "apps.core.views.custom_500"

# Добавляем обработку media-файлов при DEBUG=True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
