"""
./backend_app/admin.py
define admin page
"""
from django.contrib import admin
from .models import TaskItem

# Register your models here.
@admin.register(TaskItem)
class TaskItemAdmin(admin.ModelAdmin):
    readonly_fields = ('cel_taskid', 'hub_jobid', 'crawl_url', 'created_dt', 'ended_dt', 'full_title', 'author', 'duration', 'board')
