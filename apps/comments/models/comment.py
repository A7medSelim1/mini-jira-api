from django.db import models
from django.conf import settings
from apps.tasks.models import Task
from apps.utils.models import ActiveManager


class Comment(models.Model):
    """
    Represents a discussion comment attached to a Task.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'comment'
        verbose_name_plural = 'comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at', 'is_deleted']),
        ]

    def __str__(self):
        return f"Comment by {self.author.email} on [{self.task.task_key}]"
