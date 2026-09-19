from django.contrib import admin
from apps.activities.models import ActivityLog


@admin.register(ActivityLog)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'action', 'actor', 'project', 'task', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'actor__email', 'project__key', 'task__task_key')
    readonly_fields = ('project', 'task', 'actor', 'action', 'metadata', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
