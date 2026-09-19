from rest_framework import permissions
from apps.teams.models import TeamMembership


class HasProjectAccess(permissions.BasePermission):
    """
    Object-level permission checking if user has access to a project.
    Access granted if user is Project Reporter OR belongs to a Team in ProjectTeam.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Reporter has full project access
        if obj.reporter_id == request.user.id:
            return True

        # Check team membership in assigned project teams
        return TeamMembership.objects.filter(
            user=request.user,
            team__project_teams__project=obj
        ).exists()


class IsProjectReporter(permissions.BasePermission):
    """
    Permission checking if user is the Project Reporter/Owner.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return obj.reporter_id == request.user.id
