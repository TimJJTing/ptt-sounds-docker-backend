"""
./backend_app/urls.py
backend_app URL Configuration
Url patterns for ./backend_app/views.py
"""
from django.urls import re_path, path
from . import views
#from django.conf.urls.static import static

app_name = 'api'

urlpatterns = [
    re_path(
        r'^schedule_task/$',
        views.schedule_task,
        name='schedule_task'
    ),
    path(
        'task_progress/<int:tid>/',
        views.current_task_status,
        name='current_task_status'
    ),
    re_path(
        r'^tasks/$',
        views.TaskListView.as_view(),
        name='task_list'
    ),
    path(
        'tasks/<int:pk>/',
        views.TaskDetailView.as_view(),
        name='task_detail'
    ),
    path('', views.index),
]
