from django.db import models
from apps.projects.models.project import Project
from apps.teams.models import Team


class ProjectTeam(models.Model):
    """
    Junction entity assigning Teams to Projects.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_teams'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='project_teams'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'project team assignment'
        verbose_name_plural = 'project team assignments'
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(fields=['project', 'team'], name='unique_project_team')
        ]
        indexes = [
            models.Index(fields=['project', 'team']),
            models.Index(fields=['team', 'project']),
        ]

    def __str__(self):
        return f"Team '{self.team.name}' -> Project '{self.project.key}'"
