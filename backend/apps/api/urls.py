from django.urls import path
from .views import search_clients

urlpatterns = [
    path("search-clients/", search_clients, name="search_clients"),
]
