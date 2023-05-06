from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'clients', views.ClientViewSet)
router.register(r'contacts', views.ContactsViewSet)
router.register(r'connect_info', views.ConnectInfoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('contacts/client/<int:client_id>', views.ContactsByClientIdView.as_view(), name='contacts_by_client'),
    path('contacts/detail/<int:pk>', views.ContactDetailsView.as_view(), name='contact_details'),
]

app_name = 'rest_api'
