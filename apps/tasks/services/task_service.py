from django.db import transaction
from django.db.models import Max
from django.core.exceptions import ValidationError, PermissionDenied
from apps.tasks.models import Task, TaskStatus, TaskPriority
from apps.projects.models import Project
from apps.activities.models import ActivityLog, ActivityAction
from apps.teams.models import TeamMembership
from apps.tasks.permissions import CanTransitionTask
from apps.accounts.models import User


class TaskService:
    """
    Business service layer for Task creation, assignment, and atomic state transitions.
    """

    @staticmethod
    def is_assignee_eligible(project: Project, user: User) -> bool:
        """
        Checks if a user is eligible to be assigned a task in the project.
        User must be project reporter OR a member of a team assigned to the project.
        """
        if not user or not user.is_active:
            return False

        if project.reporter_id == user.id:
            return True

        return TeamMembership.objects.filter(
            user=user,
            team__project_teams__project=project
        ).exists()

    @staticmethod
    @transaction.atomic
    def create_task(
        project: Project,
        title: str,
        created_by: User,
        description: str = '',
        priority: str = TaskPriority.MEDIUM,
        assignee: User = None
    ) -> Task:
        """
        Creates a task with auto-incrementing sequence_number and logs activity.
        """
        if assignee and not TaskService.is_assignee_eligible(project, assignee):
            raise ValidationError({'assignee': 'Assignee must belong to a team assigned to this project.'})

        # Lock max sequence calculation per project to avoid collisions
        max_seq = Task.all_objects.filter(project=project).select_for_update().aggregate(
            max_num=Max('sequence_number')
        )['max_num'] or 0
        seq = max_seq + 1

        task_key = f"{project.key}-{seq}"

        task = Task.objects.create(
            task_key=task_key,
            sequence_number=seq,
            title=title.strip(),
            description=description,
            project=project,
            created_by=created_by,
            assignee=assignee,
            priority=priority,
            status=TaskStatus.TODO
        )

        ActivityLog.objects.create(
            project=project,
            task=task,
            actor=created_by,
            action=ActivityAction.TASK_CREATED,
            metadata={
                'task_key': task.task_key,
                'title': task.title,
                'status': task.status
            }
        )

        return task

    @staticmethod
    @transaction.atomic
    def transition_task(task_id: int, target_status: str, actor: User) -> Task:
        """
        Executes an atomic status transition with row locking and permission checking.
        """
        task = Task.objects.select_for_update().select_related('project').get(id=task_id)

        if task.status == target_status:
            return task

        if not CanTransitionTask.is_authorized(task, target_status, actor):
            raise PermissionDenied(
                f"User is not authorized to transition task from '{task.status}' to '{target_status}'."
            )

        old_status = task.status
        task.status = target_status
        task.save()

        ActivityLog.objects.create(
            project=task.project,
            task=task,
            actor=actor,
            action=ActivityAction.TASK_STATUS_CHANGED,
            metadata={
                'task_key': task.task_key,
                'from_status': old_status,
                'to_status': target_status
            }
        )

        return task

    @staticmethod
    @transaction.atomic
    def assign_task(task_id: int, assignee: User | None, actor: User) -> Task:
        """
        Assigns or unassigns a task to an eligible user.
        """
        task = Task.objects.select_for_update().select_related('project').get(id=task_id)

        if assignee and not TaskService.is_assignee_eligible(task.project, assignee):
            raise ValidationError({'assignee': 'Assignee must belong to a team assigned to this project.'})

        old_assignee_email = task.assignee.email if task.assignee else None
        task.assignee = assignee
        task.save()

        new_assignee_email = assignee.email if assignee else None

        ActivityLog.objects.create(
            project=task.project,
            task=task,
            actor=actor,
            action=ActivityAction.TASK_ASSIGNED,
            metadata={
                'task_key': task.task_key,
                'old_assignee': old_assignee_email,
                'new_assignee': new_assignee_email
            }
        )

        return task
