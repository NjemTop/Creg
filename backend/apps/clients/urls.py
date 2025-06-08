from django.urls import path
from . import views


app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('<int:client_id>/', views.client_detail, name='client_detail'),
    path("create/", views.create_client, name="create_client"),
]
