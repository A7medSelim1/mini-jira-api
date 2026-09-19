from django.db import models
from django.conf import settings
from apps.teams.models.team import Team


class TeamMembership(models.Model):
    """
    Junction entity representing membership of a user in a team.
    """
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'team membership'
        verbose_name_plural = 'team memberships'
        ordering = ['-joined_at']
        constraints = [
            models.UniqueConstraint(fields=['team', 'user'], name='unique_team_membership')
        ]
        indexes = [
            models.Index(fields=['team', 'user']),
            models.Index(fields=['user', 'team']),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.team.name}"
