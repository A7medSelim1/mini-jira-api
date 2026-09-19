from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.comments.models import Comment
from apps.tasks.models import Task
from apps.activities.models import ActivityLog, ActivityAction
from apps.accounts.models import User


class CommentService:
    """
    Business service layer for Comment operations and activity logging.
    """

    @staticmethod
    @transaction.atomic
    def add_comment(task: Task, author: User, content: str) -> Comment:
        """
        Adds a comment to a task and logs activity.
        """
        content = content.strip()
        if not content:
            raise ValidationError({'content': 'Comment content cannot be blank.'})

        comment = Comment.objects.create(
            task=task,
            author=author,
            content=content
        )

        ActivityLog.objects.create(
            project=task.project,
            task=task,
            actor=author,
            action=ActivityAction.COMMENT_ADDED,
            metadata={
                'comment_id': comment.id,
                'task_key': task.task_key
            }
        )

        return comment

    @staticmethod
    @transaction.atomic
    def soft_delete_comment(comment: Comment, actor: User) -> None:
        """
        Soft deletes a comment and logs activity.
        """
        comment.is_deleted = True
        comment.deleted_at = timezone.now()
        comment.save()

        ActivityLog.objects.create(
            project=comment.task.project,
            task=comment.task,
            actor=actor,
            action=ActivityAction.COMMENT_DELETED,
            metadata={
                'comment_id': comment.id,
                'task_key': comment.task.task_key
            }
        )
