from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'clients', views.ClientsViewSet)
router.register(r'connect_info', views.ConnectInfoViewSet, basename='connect_info')

urlpatterns = [
    path('', include(router.urls)),
    path('contacts/', views.ContactsViewSet.as_view({'get': 'list_all'})),
    path('contacts/<int:client_id>/', views.ContactsViewSet.as_view({'get': 'list'})),
]

app_name = 'rest_api'
