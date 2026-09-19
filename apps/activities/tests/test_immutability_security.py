from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.activities.models import ActivityLog, ActivityAction
from apps.tasks.services import TaskService


class ActivityImmutabilitySecurityTest(APITestCase):
    """
    Security test suite verifying ActivityLog immutability, transaction consistency,
    and HTTP 405 Method Not Allowed blocking on write operations.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(key='IMMUT', title='Immutable Project', reporter=self.reporter)
        self.task = Task.objects.create(
            task_key='IMMUT-1', sequence_number=1, title='Audit Task',
            project=self.project, created_by=self.reporter
        )
        self.log = ActivityLog.objects.create(
            project=self.project,
            task=self.task,
            actor=self.reporter,
            action=ActivityAction.TASK_CREATED,
            metadata={'title': 'Audit Task'}
        )

        self.project_activities_url = reverse('project-activities-list', kwargs={'project_id': self.project.id})

    def test_model_save_update_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.log.action = ActivityAction.TASK_UPDATED
            self.log.save()

    def test_model_delete_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.log.delete()

    def test_api_post_activity_returns_method_not_allowed(self):
        self.client.force_authenticate(user=self.reporter)
        res = self.client.post(self.project_activities_url, {'action': 'FAKE_ACTION'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_api_put_activity_returns_method_not_allowed(self):
        self.client.force_authenticate(user=self.reporter)
        res = self.client.put(self.project_activities_url, {'action': 'FAKE_ACTION'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_api_delete_activity_returns_method_not_allowed(self):
        self.client.force_authenticate(user=self.reporter)
        res = self.client.delete(self.project_activities_url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_failed_api_task_creation_does_not_create_activity_log(self):
        initial_count = ActivityLog.objects.count()
        url = reverse('project-tasks-list-create', kwargs={'project_id': self.project.id})

        self.client.force_authenticate(user=self.reporter)
        # Attempting to assign ineligible user via API
        res = self.client.post(url, {
            'title': 'Bad Task',
            'assignee_id': self.outsider.id
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ActivityLog.objects.count(), initial_count)
