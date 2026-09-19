from django.contrib import admin
from apps.comments.models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'author', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('content', 'author__email', 'task__task_key')
    list_filter = ('is_deleted', 'created_at')
    raw_id_fields = ('task', 'author')
