from django.db.models import QuerySet
from apps.activities.models import ActivityLog
from apps.projects.selectors import ProjectSelector
from apps.tasks.selectors import TaskSelector


class ActivitySelector:
    """
    IDOR-protected selector for ActivityLog read queries.
    """

    @staticmethod
    def get_project_activities(project_id: int, user) -> QuerySet[ActivityLog]:
        """
        Returns audit logs for a project if user has project access.
        """
        project = ProjectSelector.get_project_by_id(project_id, user)
        if not project:
            return ActivityLog.objects.none()

        return ActivityLog.objects.filter(
            project=project
        ).select_related('project', 'task', 'actor')

    @staticmethod
    def get_task_activities(task_id: int, user) -> QuerySet[ActivityLog]:
        """
        Returns audit logs for a task if user has access to the task's project.
        """
        task = TaskSelector.get_task_by_id(task_id, user)
        if not task:
            return ActivityLog.objects.none()

        return ActivityLog.objects.filter(
            task=task
        ).select_related('project', 'task', 'actor')
