from django.urls import path
from . import views


app_name = 'mailing'

urlpatterns = [
    path('', views.mailing_list, name='mailing_list'),
    path('create/', views.create_mailing, name='create_mailing'),
    path('edit/<int:mailing_id>/', views.edit_mailing, name='edit_mailing'),
    path('start/<int:mailing_id>/', views.start_mailing, name='start_mailing'),
    path('detail/<int:mailing_id>/', views.mailing_detail, name='mailing_detail'),
    path('stop/<int:mailing_id>/', views.stop_mailing, name='stop_mailing'),
    path('repeat/<int:mailing_id>/', views.repeat_mailing, name='repeat_mailing'),
]
