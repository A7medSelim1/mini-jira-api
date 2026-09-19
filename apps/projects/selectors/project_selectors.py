from django.db.models import QuerySet, Q
from apps.projects.models import Project


class ProjectSelector:
    """
    IDOR-protected selector for Project read queries.
    """

    @staticmethod
    def get_user_projects(user) -> QuerySet[Project]:
        """
        Returns all projects accessible to the user (as Reporter or Team Member).
        """
        if not user or not user.is_authenticated:
            return Project.objects.none()

        return Project.objects.filter(
            Q(reporter=user) | Q(project_teams__team__memberships__user=user)
        ).select_related('reporter').prefetch_related('project_teams__team').distinct()

    @staticmethod
    def get_project_by_id(project_id: int, user) -> Project | None:
        """
        Retrieves project by ID ensuring user has backend access.
        """
        if not user or not user.is_authenticated:
            return None

        try:
            return ProjectSelector.get_user_projects(user).get(id=project_id)
        except Project.DoesNotExist:
            return None
