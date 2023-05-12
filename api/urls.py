from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'clients', views.ClientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('add_client', views.add_client, name='add_client'),
    path('contacts/client/<int:client_id>', views.ContactsByClientIdView.as_view(), name='contacts_by_client'),
    path('contacts/detail/<int:pk>', views.ContactDetailsView.as_view(), name='contact_details'),
    path('connect_info/client/<int:client_id>', views.ConnectInfoByClientIdView.as_view(), name='connect_info_by_client'),
    path('connect_info/detail/<int:pk>', views.ConnectInfoDetailsView.as_view(), name='connect_info_details'),
    path('bm_servers/client/<int:client_id>', views.BMServersByClientIdView.as_view(), name='bm_servers_by_client_id'),
    path('bm_servers/detail/<int:pk>', views.BMServersDetailsView.as_view(), name='bm_servers_details'),
    path('integration/client/<int:client_id>', views.IntegrationByClientIdView.as_view(), name='integration_by_client'),
    path('integration/detail/<int:pk>', views.IntegrationDetailsView.as_view(), name='integration_details'),
    path('tech_account/client/<int:client_id>', views.TechAccountByClientIdView.as_view(), name='tech_account_by_client'),
    path('tech_account/detail/<int:pk>', views.TechAccountDetailsView.as_view(), name='tech_account_details'),
    path('upload_file/<int:client_id>', views.FileUploadView.as_view(), name='upload_file'),
    path('client_files/<int:client_id>', views.ClientFilesView.as_view(), name='client_files'),
    path('client_files/detail/<int:pk>', views.FileUploadView.as_view(), name='client_files_detail'),
    path('servise/client/<int:client_id>', views.ServiseByClientIdView.as_view(), name='servise_by_client'),
    path('servise/detail/<int:pk>', views.ServiseDetailsView.as_view(), name='servise_details'),
    path('tech_information/client/<int:client_id>', views.TechInformationByClientIdView.as_view(), name='tech_information_by_client'),
    path('tech_information/detail/<int:pk>', views.TechInformationDetailsView.as_view(), name='tech_information_details'),
    path('tech_note/client/<int:client_id>', views.TechNoteByClientIdView.as_view(), name='tech_note_by_client'),
    path('tech_note/detail/<int:pk>', views.TechNoteDetailsView.as_view(), name='tech_note_details'),
] + router.urls

app_name = 'rest_api'
