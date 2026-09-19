from rest_framework import permissions
from apps.teams.models import TeamMembership


class IsTeamMember(permissions.BasePermission):
    """
    Object-level permission checking if user belongs to the target team.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return TeamMembership.objects.filter(team=obj, user=request.user).exists()
