from django.db.models import QuerySet, Count
from apps.teams.models import Team, TeamMembership


class TeamSelector:
    """
    Query selector for optimized Team read operations.
    """

    @staticmethod
    def get_all_teams() -> QuerySet[Team]:
        return Team.objects.select_related('created_by').annotate(
            member_count=Count('memberships', distinct=True)
        )

    @staticmethod
    def get_user_teams(user) -> QuerySet[Team]:
        """
        Returns teams that the specified user belongs to or created.
        """
        return Team.objects.filter(
            memberships__user=user
        ).select_related('created_by').annotate(
            member_count=Count('memberships', distinct=True)
        ).distinct()

    @staticmethod
    def get_team_by_id(team_id: int) -> Team | None:
        try:
            return Team.objects.select_related('created_by').annotate(
                member_count=Count('memberships', distinct=True)
            ).get(id=team_id)
        except Team.DoesNotExist:
            return None

    @staticmethod
    def get_team_members(team_id: int) -> QuerySet[TeamMembership]:
        return TeamMembership.objects.filter(
            team_id=team_id
        ).select_related('user', 'team')
