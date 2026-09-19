from rest_framework import permissions
from apps.tasks.models import TaskStatus
from apps.teams.models import TeamMembership


class HasTaskAccess(permissions.BasePermission):
    """
    Object-level permission checking if user has access to a task via its project.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        project = obj.project
        if project.reporter_id == request.user.id:
            return True

        return TeamMembership.objects.filter(
            user=request.user,
            team__project_teams__project=project
        ).exists()


class CanTransitionTask:
    """
    Evaluates whether an actor is authorized to transition a task from current_status to target_status.
    """
    @staticmethod
    def is_authorized(task, target_status: str, actor) -> bool:
        if not actor or not actor.is_authenticated:
            return False

        project = task.project
        is_reporter = (project.reporter_id == actor.id)
        is_assignee = (task.assignee_id == actor.id)

        current_status = task.status

        # Transition rules
        if current_status == TaskStatus.TODO and target_status == TaskStatus.IN_PROGRESS:
            return is_assignee or is_reporter

        if current_status == TaskStatus.IN_PROGRESS and target_status == TaskStatus.READY_FOR_REVIEW:
            return is_assignee or is_reporter

        if current_status == TaskStatus.READY_FOR_REVIEW and target_status == TaskStatus.DONE:
            # Reporter ONLY
            return is_reporter

        if current_status == TaskStatus.READY_FOR_REVIEW and target_status == TaskStatus.TODO:
            # Reporter ONLY (Rejection)
            return is_reporter

        return False
