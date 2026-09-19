from django.test import TestCase
from django.db.utils import IntegrityError
from apps.accounts.models import User
from apps.projects.models import Project
from apps.tasks.models import Task, TaskStatus, TaskPriority


class TaskModelTest(TestCase):
    """
    Unit tests for Task model.
    """

    def setUp(self):
        self.user = User.objects.create_user(email='creator@example.com', password='Password123!')
        self.project = Project.objects.create(key='JIRA', title='Mini Jira', reporter=self.user)

    def test_create_task(self):
        task = Task.objects.create(
            task_key='JIRA-1',
            sequence_number=1,
            title='Setup Project DB',
            project=self.project,
            created_by=self.user,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH
        )
        self.assertEqual(task.task_key, 'JIRA-1')
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(str(task), '[JIRA-1] Setup Project DB')

    def test_unique_task_key_constraint(self):
        Task.objects.create(
            task_key='JIRA-1',
            sequence_number=1,
            title='Task 1',
            project=self.project,
            created_by=self.user
        )
        with self.assertRaises(IntegrityError):
            Task.objects.create(
                task_key='JIRA-1',
                sequence_number=2,
                title='Task 2',
                project=self.project,
                created_by=self.user
            )

    def test_unique_project_sequence_constraint(self):
        Task.objects.create(
            task_key='JIRA-1',
            sequence_number=1,
            title='Task 1',
            project=self.project,
            created_by=self.user
        )
        with self.assertRaises(IntegrityError):
            Task.objects.create(
                task_key='JIRA-2',
                sequence_number=1,
                title='Task 2 Duplicate Seq',
                project=self.project,
                created_by=self.user
            )
