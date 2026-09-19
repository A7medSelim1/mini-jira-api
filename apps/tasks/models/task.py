from django.db import models
from django.conf import settings
from apps.projects.models import Project
from apps.utils.models import ActiveManager


class TaskStatus(models.TextChoices):
    TODO = 'TODO', 'To Do'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    READY_FOR_REVIEW = 'READY_FOR_REVIEW', 'Ready For Review'
    DONE = 'DONE', 'Done'


class TaskPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'


class Task(models.Model):
    """
    Represents a Task/Card belonging to a Project.
    """
    task_key = models.CharField(max_length=30, unique=True, db_index=True)
    sequence_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tasks'
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    status = models.CharField(
        max_length=30,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM,
        db_index=True
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'task'
        verbose_name_plural = 'tasks'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['task_key'], name='unique_task_key'),
            models.UniqueConstraint(fields=['project', 'sequence_number'], name='unique_project_task_sequence'),
            models.CheckConstraint(
                condition=models.Q(status__in=TaskStatus.values),
                name='valid_task_status'
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=TaskPriority.values),
                name='valid_task_priority'
            ),
        ]
        indexes = [
            models.Index(fields=['project', 'status', 'is_deleted']),
            models.Index(fields=['project', 'assignee', 'is_deleted']),
            models.Index(fields=['project', 'priority', 'is_deleted']),
            models.Index(fields=['project', 'created_at', 'is_deleted']),
            models.Index(fields=['assignee', 'is_deleted']),
        ]

    def __str__(self):
        return f"[{self.task_key}] {self.title}"
