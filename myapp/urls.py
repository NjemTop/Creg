from django.urls import path
from . import views

urlpatterns = [
    path('get_clients/', views.get_clients, name='get_clients'),
    path('add_client/', views.add_client, name='add_client'),
]
