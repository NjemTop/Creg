from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_clients/', views.get_clients, name='get_clients'),
    path('add_client/', views.add_client, name='add_client'),
    path('get_client/<int:client_id>/', views.get_client, name='get_client'),
    path('search_clients/', views.search_clients, name='search_clients'),
]
