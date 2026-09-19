from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, TaskStatus, TaskPriority
from apps.activities.models import ActivityLog, ActivityAction


class TaskViewsTest(APITestCase):
    """
    API integration tests for Task endpoints and controlled workflow transitions.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.assignee = User.objects.create_user(email='assignee@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(key='CARD', title='Card Project', reporter=self.reporter)
        self.team = Team.objects.create(name='Card Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.assignee)
        ProjectTeam.objects.create(project=self.project, team=self.team)

        self.project_tasks_url = reverse('project-tasks-list-create', kwargs={'project_id': self.project.id})

    def test_create_task_api_success(self):
        self.client.force_authenticate(user=self.assignee)
        payload = {
            'title': 'Implement Auth Views',
            'description': 'Details',
            'priority': TaskPriority.HIGH,
            'assignee_id': self.assignee.id
        }
        response = self.client.post(self.project_tasks_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['task_key'], 'CARD-1')
        self.assertEqual(response.data['data']['status'], TaskStatus.TODO)

        # Verify activity created
        self.assertTrue(ActivityLog.objects.filter(project=self.project, action=ActivityAction.TASK_CREATED).exists())

    def test_create_task_ineligible_assignee_fails(self):
        self.client.force_authenticate(user=self.reporter)
        payload = {
            'title': 'Invalid Assignee Task',
            'assignee_id': self.outsider.id
        }
        response = self.client.post(self.project_tasks_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_patch_status_update_rejected(self):
        task = Task.objects.create(
            task_key='CARD-1',
            sequence_number=1,
            title='Test Task',
            project=self.project,
            created_by=self.reporter
        )
        url = reverse('task-detail', kwargs={'pk': task.id})

        self.client.force_authenticate(user=self.reporter)
        response = self.client.patch(url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('PATCH', response.data['error']['message'])

    def test_controlled_status_transition_workflow(self):
        task = Task.objects.create(
            task_key='CARD-1',
            sequence_number=1,
            title='Workflow Task',
            project=self.project,
            created_by=self.reporter,
            assignee=self.assignee,
            status=TaskStatus.TODO
        )
        transition_url = reverse('task-transition', kwargs={'pk': task.id})

        # 1. Assignee transitions TODO -> IN_PROGRESS
        self.client.force_authenticate(user=self.assignee)
        res1 = self.client.post(transition_url, {'status': TaskStatus.IN_PROGRESS}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data['data']['status'], TaskStatus.IN_PROGRESS)

        # 2. Assignee transitions IN_PROGRESS -> READY_FOR_REVIEW
        res2 = self.client.post(transition_url, {'status': TaskStatus.READY_FOR_REVIEW}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['data']['status'], TaskStatus.READY_FOR_REVIEW)

        # 3. Assignee attempts READY_FOR_REVIEW -> DONE (FORBIDDEN)
        res3 = self.client.post(transition_url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(res3.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Reporter approves READY_FOR_REVIEW -> DONE (SUCCESS)
        self.client.force_authenticate(user=self.reporter)
        res4 = self.client.post(transition_url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(res4.status_code, status.HTTP_200_OK)
        self.assertEqual(res4.data['data']['status'], TaskStatus.DONE)

    def test_invalid_status_transition_returns_error(self):
        task = Task.objects.create(
            task_key='CARD-1',
            sequence_number=1,
            title='Direct Jump Task',
            project=self.project,
            created_by=self.reporter,
            status=TaskStatus.TODO
        )
        transition_url = reverse('task-transition', kwargs={'pk': task.id})

        self.client.force_authenticate(user=self.reporter)
        # Attempt direct jump TODO -> DONE
        response = self.client.post(transition_url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_assignment_api(self):
        task = Task.objects.create(
            task_key='CARD-1',
            sequence_number=1,
            title='Unassigned Task',
            project=self.project,
            created_by=self.reporter
        )
        assign_url = reverse('task-assign', kwargs={'pk': task.id})

        self.client.force_authenticate(user=self.reporter)
        response = self.client.post(assign_url, {'assignee_id': self.assignee.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['assignee']['email'], self.assignee.email)
