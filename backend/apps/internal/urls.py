from django.urls import path
from .views import ws_test_page

urlpatterns = [
    path('test-ws/', ws_test_page, name='test_ws_page'),
]
