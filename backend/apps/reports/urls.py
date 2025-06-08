from django.urls import path
from . import views


app_name = 'reports'

urlpatterns = [
    path('', views.report, name='report'),
    path('release_info/', views.release_info, name='release_info'),
]
