from django.test import TestCase
from django.core.exceptions import PermissionDenied
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, TaskStatus
from apps.tasks.services import TaskService
from apps.tasks.permissions import CanTransitionTask, HasTaskAccess
from apps.tasks.selectors import TaskSelector


class TaskPermissionsTest(TestCase):
    def setUp(self):
        self.reporter = User.objects.create_user(email='rep@example.com', password='Password123!')
        self.assignee = User.objects.create_user(email='assignee@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(key='FLOW', title='Flow Project', reporter=self.reporter)
        self.team = Team.objects.create(name='Flow Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.assignee)
        ProjectTeam.objects.create(project=self.project, team=self.team)

        self.task = TaskService.create_task(
            project=self.project,
            title='Workflow Task',
            created_by=self.reporter,
            assignee=self.assignee
        )

    def test_todo_to_in_progress_by_assignee_allowed(self):
        self.assertTrue(CanTransitionTask.is_authorized(self.task, TaskStatus.IN_PROGRESS, self.assignee))
        updated_task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.assertEqual(updated_task.status, TaskStatus.IN_PROGRESS)

    def test_in_progress_to_ready_for_review_by_assignee_allowed(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.assertTrue(CanTransitionTask.is_authorized(self.task, TaskStatus.READY_FOR_REVIEW, self.assignee))
        updated_task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)
        self.assertEqual(updated_task.status, TaskStatus.READY_FOR_REVIEW)

    def test_ready_for_review_to_done_by_assignee_forbidden(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)

        self.assertFalse(CanTransitionTask.is_authorized(self.task, TaskStatus.DONE, self.assignee))
        with self.assertRaises(PermissionDenied):
            TaskService.transition_task(self.task.id, TaskStatus.DONE, self.assignee)

    def test_ready_for_review_to_done_by_reporter_allowed(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)

        self.assertTrue(CanTransitionTask.is_authorized(self.task, TaskStatus.DONE, self.reporter))
        updated_task = TaskService.transition_task(self.task.id, TaskStatus.DONE, self.reporter)
        self.assertEqual(updated_task.status, TaskStatus.DONE)

    def test_ready_for_review_rejection_by_reporter_allowed(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)

        self.assertTrue(CanTransitionTask.is_authorized(self.task, TaskStatus.TODO, self.reporter))
        updated_task = TaskService.transition_task(self.task.id, TaskStatus.TODO, self.reporter)
        self.assertEqual(updated_task.status, TaskStatus.TODO)

    def test_task_selector_idor_protection(self):
        # Assignee & Reporter see task
        self.assertIsNotNone(TaskSelector.get_task_by_id(self.task.id, self.reporter))
        self.assertIsNotNone(TaskSelector.get_task_by_id(self.task.id, self.assignee))
        # Outsider gets None
        self.assertIsNone(TaskSelector.get_task_by_id(self.task.id, self.outsider))
