from django.urls import path
from . import views


app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('contacts/', views.contacts, name='contacts'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
]
