from django.urls import path
from . import views

urlpatterns = [
    path('creation_tickets/', views.creation_tickets, name='creation_tickets'),
    path('open_tickets/', views.open_tickets, name='open_tickets'),
    path('tech_account/add/<int:client_id>/', views.add_tech_account, name='add_tech_account'),
    path('tech_account/update/<int:account_id>/', views.update_tech_account, name='update_tech_account'),
    path('tech_account/delete/<int:account_id>/', views.delete_tech_account, name='delete_tech_account'),
    path('connect_info/add/<int:client_id>/', views.add_connect_info, name='add_connect_info'),
    path('connect_info/update/<int:connect_info_id>/', views.update_connect_info, name='update_connect_info'),
    path('connect_info/delete/<int:connect_info_id>/', views.delete_connect_info, name='delete_connect_info'),
    path('contact/add/<int:client_id>/', views.add_contact, name='add_contact'),
    path('contact/update/<int:contact_id>/', views.update_contact, name='update_contact'),
]
