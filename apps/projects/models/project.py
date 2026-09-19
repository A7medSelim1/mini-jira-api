from django.db import models
from django.conf import settings
from apps.utils.models import ActiveManager


class Project(models.Model):
    """
    Represents a Project workspace owned by a Reporter.
    """
    key = models.CharField(max_length=10, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reported_projects'
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'project'
        verbose_name_plural = 'projects'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['key'], name='unique_project_key'),
            models.CheckConstraint(
                condition=models.Q(key__regex=r'^[A-Z0-9]+$'),
                name='project_key_must_be_uppercase_alphanumeric'
            )
        ]
        indexes = [
            models.Index(fields=['reporter', 'is_deleted']),
            models.Index(fields=['key', 'is_deleted']),
        ]

    def __str__(self):
        return f"[{self.key}] {self.title}"

    def save(self, *args, **kwargs):
        if self.key:
            self.key = self.key.upper().strip()
        super().save(*args, **kwargs)
