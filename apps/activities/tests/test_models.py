from django.test import TestCase
from apps.accounts.models import User
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.activities.models import ActivityLog, ActivityAction


class ActivityLogModelTest(TestCase):
    """
    Unit tests for ActivityLog model.
    """

    def setUp(self):
        self.user = User.objects.create_user(email='actor@example.com', password='Password123!')
        self.project = Project.objects.create(key='LOG', title='Log Project', reporter=self.user)
        self.task = Task.objects.create(
            task_key='LOG-1',
            sequence_number=1,
            title='Log Task',
            project=self.project,
            created_by=self.user
        )

    def test_create_activity_log(self):
        log = ActivityLog.objects.create(
            project=self.project,
            task=self.task,
            actor=self.user,
            action=ActivityAction.TASK_CREATED,
            metadata={'title': 'Log Task'}
        )
        self.assertEqual(log.action, ActivityAction.TASK_CREATED)
        self.assertEqual(log.metadata['title'], 'Log Task')

    def test_activity_log_immutable_save_raises_error(self):
        log = ActivityLog.objects.create(
            project=self.project,
            task=self.task,
            actor=self.user,
            action=ActivityAction.TASK_CREATED
        )
        with self.assertRaises(ValueError):
            log.action = ActivityAction.TASK_UPDATED
            log.save()

    def test_activity_log_immutable_delete_raises_error(self):
        log = ActivityLog.objects.create(
            project=self.project,
            task=self.task,
            actor=self.user,
            action=ActivityAction.TASK_CREATED
        )
        with self.assertRaises(ValueError):
            log.delete()
