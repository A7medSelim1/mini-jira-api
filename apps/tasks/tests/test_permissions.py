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
        # Project Reporter (Ahmed)
        self.project_reporter = User.objects.create_user(email='ahmed@example.com', password='Password123!')
        # Task Reporter / Creator (Mohammed)
        self.task_reporter = User.objects.create_user(email='mohammed@example.com', password='Password123!')
        # Assignee (Omar)
        self.assignee = User.objects.create_user(email='omar@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(key='FLOW', title='Flow Project', reporter=self.project_reporter)
        self.team = Team.objects.create(name='Flow Team', created_by=self.project_reporter)
        TeamMembership.objects.create(team=self.team, user=self.task_reporter)
        TeamMembership.objects.create(team=self.team, user=self.assignee)
        ProjectTeam.objects.create(project=self.project, team=self.team)

        # Mohammed (task_reporter) creates the task
        self.task = TaskService.create_task(
            project=self.project,
            title='Workflow Task',
            created_by=self.task_reporter,
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

    def test_1_task_creator_reporter_can_approve_done(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)

        self.assertTrue(CanTransitionTask.is_authorized(self.task, TaskStatus.DONE, self.task_reporter))
        updated_task = TaskService.transition_task(self.task.id, TaskStatus.DONE, self.task_reporter)
        self.assertEqual(updated_task.status, TaskStatus.DONE)

    def test_2_assignee_cannot_approve_done(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)

        self.assertFalse(CanTransitionTask.is_authorized(self.task, TaskStatus.DONE, self.assignee))
        with self.assertRaises(PermissionDenied):
            TaskService.transition_task(self.task.id, TaskStatus.DONE, self.assignee)

    def test_3_project_reporter_cannot_approve_another_users_task_unless_task_reporter(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)

        # Ahmed (project_reporter) is NOT Mohammed (task_reporter)
        self.assertFalse(CanTransitionTask.is_authorized(self.task, TaskStatus.DONE, self.project_reporter))
        with self.assertRaises(PermissionDenied):
            TaskService.transition_task(self.task.id, TaskStatus.DONE, self.project_reporter)

    def test_4_task_reporter_can_reject_ready_for_review_back_to_todo(self):
        self.task = TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.assignee)
        self.task = TaskService.transition_task(self.task.id, TaskStatus.READY_FOR_REVIEW, self.assignee)

        self.assertTrue(CanTransitionTask.is_authorized(self.task, TaskStatus.TODO, self.task_reporter))
        updated_task = TaskService.transition_task(self.task.id, TaskStatus.TODO, self.task_reporter)
        self.assertEqual(updated_task.status, TaskStatus.TODO)

    def test_task_selector_idor_protection(self):
        # Assignee & Reporters see task
        self.assertIsNotNone(TaskSelector.get_task_by_id(self.task.id, self.task_reporter))
        self.assertIsNotNone(TaskSelector.get_task_by_id(self.task.id, self.assignee))
        # Outsider gets None
        self.assertIsNone(TaskSelector.get_task_by_id(self.task.id, self.outsider))
