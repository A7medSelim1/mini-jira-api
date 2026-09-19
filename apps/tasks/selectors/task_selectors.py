from django.db.models import QuerySet, Q
from apps.tasks.models import Task
from apps.projects.selectors import ProjectSelector


class TaskSelector:
    """
    IDOR-protected selector for Task read queries.
    """

    @staticmethod
    def get_user_tasks(user) -> QuerySet[Task]:
        """
        Returns tasks across all projects accessible to the user.
        """
        if not user or not user.is_authenticated:
            return Task.objects.none()

        accessible_projects = ProjectSelector.get_user_projects(user)
        return Task.objects.filter(
            project__in=accessible_projects
        ).select_related('project', 'created_by', 'assignee')

    @staticmethod
    def get_project_tasks(project_id: int, user) -> QuerySet[Task]:
        """
        Returns tasks for a project if user has access to the project.
        """
        project = ProjectSelector.get_project_by_id(project_id, user)
        if not project:
            return Task.objects.none()

        return Task.objects.filter(
            project=project
        ).select_related('project', 'created_by', 'assignee')

    @staticmethod
    def get_task_by_id(task_id: int, user) -> Task | None:
        """
        Retrieves task by ID ensuring user has project access.
        """
        if not user or not user.is_authenticated:
            return None

        try:
            task = Task.objects.select_related('project', 'created_by', 'assignee').get(id=task_id)
            if ProjectSelector.get_project_by_id(task.project_id, user):
                return task
            return None
        except Task.DoesNotExist:
            return None
