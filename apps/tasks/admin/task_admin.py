from django.contrib import admin
from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_key', 'title', 'project', 'status', 'priority', 'assignee', 'created_by', 'is_deleted')
    list_filter = ('status', 'priority', 'is_deleted', 'created_at')
    search_fields = ('task_key', 'title', 'description', 'project__key')
    raw_id_fields = ('project', 'created_by', 'assignee')
