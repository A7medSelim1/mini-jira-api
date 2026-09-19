from django.db.models import QuerySet
from apps.comments.models import Comment
from apps.tasks.selectors import TaskSelector


class CommentSelector:
    """
    IDOR-protected selector for Comment read queries.
    """

    @staticmethod
    def get_task_comments(task_id: int, user) -> QuerySet[Comment]:
        """
        Returns comments for a task if user has access to the task's project.
        """
        task = TaskSelector.get_task_by_id(task_id, user)
        if not task:
            return Comment.objects.none()

        return Comment.objects.filter(task=task).select_related('author', 'task')
