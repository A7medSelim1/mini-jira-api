from django.db import models
from django.conf import settings
from apps.projects.models import Project
from apps.tasks.models import Task


class ActivityAction(models.TextChoices):
    PROJECT_CREATED = 'PROJECT_CREATED', 'Project Created'
    PROJECT_UPDATED = 'PROJECT_UPDATED', 'Project Updated'
    PROJECT_TEAM_ADDED = 'PROJECT_TEAM_ADDED', 'Team Assigned to Project'
    PROJECT_TEAM_REMOVED = 'PROJECT_TEAM_REMOVED', 'Team Removed from Project'
    TASK_CREATED = 'TASK_CREATED', 'Task Created'
    TASK_UPDATED = 'TASK_UPDATED', 'Task Details Updated'
    TASK_ASSIGNED = 'TASK_ASSIGNED', 'Task Assignee Changed'
    TASK_STATUS_CHANGED = 'TASK_STATUS_CHANGED', 'Task Status Changed'
    COMMENT_ADDED = 'COMMENT_ADDED', 'Comment Added'
    COMMENT_DELETED = 'COMMENT_DELETED', 'Comment Deleted'


class ActivityLog(models.Model):
    """
    Immutable audit history log recording business events across Projects and Tasks.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    action = models.CharField(
        max_length=50,
        choices=ActivityAction.choices,
        db_index=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'activity log'
        verbose_name_plural = 'activity logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['project', 'timestamp']),
            models.Index(fields=['task', 'timestamp']),
        ]

    def __str__(self):
        actor_email = self.actor.email if self.actor else 'System'
        target = f"Task [{self.task.task_key}]" if self.task else f"Project [{self.project.key}]"
        return f"{self.action} by {actor_email} on {target}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("ActivityLog entries are immutable and cannot be updated once created.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("ActivityLog entries are immutable and cannot be deleted directly.")
