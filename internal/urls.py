from django.urls import path
from . import views

urlpatterns = [
    path('', views.internal_index, name='index'),
    path('release_notes/', views.release_notes, name='release_notes'),
    path('release_notes_page/', views.release_notes_page, name='internal_release_notes_page'),
    path('show_log_download/', views.show_log_download, name='internal_show_log_download'),
    path('get_log_analysis_data/', views.get_log_analysis_data, name='get_log_analysis_data'),
    path('get_task_status/<str:task_id>/', views.get_task_status, name='get_task_status'),
    path('test_task/', views.test_task, name='internal_test_task'),
    path('test_email_task/', views.test_send_email_task, name='internal_test_email_task'),
    path('task_results/', views.task_results, name='internal_task_results'),
]
