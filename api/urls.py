from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'clients', views.ClientViewSet)
router.register(r'contacts', views.ContactsViewSet)
router.register(r'connect_info', views.ConnectInfoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

app_name = 'rest_api'
