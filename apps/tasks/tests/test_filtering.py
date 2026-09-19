from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, TaskStatus, TaskPriority


class TaskFilteringTest(APITestCase):
    """
    Exhaustive integration tests for Task filtering, searching, safe ordering,
    pagination, invalid query parameters, and security isolation.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.assignee = User.objects.create_user(email='assignee@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project1 = Project.objects.create(key='PROJ1', title='First Project', reporter=self.reporter)
        self.project2 = Project.objects.create(key='PROJ2', title='Second Project', reporter=self.reporter)
        self.secret_project = Project.objects.create(key='SECRET', title='Secret Project', reporter=self.outsider)

        self.team = Team.objects.create(name='Devs', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.assignee)
        ProjectTeam.objects.create(project=self.project1, team=self.team)
        ProjectTeam.objects.create(project=self.project2, team=self.team)

        # Create tasks in project 1
        self.t1 = Task.objects.create(
            task_key='PROJ1-1', sequence_number=1, title='Fix login bug', description='Authentication issue',
            project=self.project1, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.TODO, priority=TaskPriority.HIGH
        )
        self.t2 = Task.objects.create(
            task_key='PROJ1-2', sequence_number=2, title='Build dashboard', description='Analytics UI',
            project=self.project1, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.IN_PROGRESS, priority=TaskPriority.URGENT
        )

        # Create tasks in project 2
        self.t3 = Task.objects.create(
            task_key='PROJ2-1', sequence_number=1, title='Database migration', description='Postgres setup',
            project=self.project2, created_by=self.reporter, assignee=None,
            status=TaskStatus.TODO, priority=TaskPriority.LOW
        )

        # Create task in secret project (outsider)
        self.secret_task = Task.objects.create(
            task_key='SECRET-1', sequence_number=1, title='Hidden task',
            project=self.secret_project, created_by=self.outsider,
            status=TaskStatus.TODO, priority=TaskPriority.HIGH
        )

        self.global_tasks_url = reverse('global-task-list')
        self.project1_tasks_url = reverse('project-tasks-list-create', kwargs={'project_id': self.project1.id})

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {'status': TaskStatus.IN_PROGRESS})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['data'][0]['task_key'], 'PROJ1-2')

    def test_filter_by_priority(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {'priority': TaskPriority.HIGH})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['data'][0]['task_key'], 'PROJ1-1')

    def test_filter_by_assignee(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {'assignee': self.assignee.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_search_text(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {'search': 'analytics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['data'][0]['task_key'], 'PROJ1-2')

    def test_safe_ordering_title_asc_and_desc(self):
        self.client.force_authenticate(user=self.assignee)
        # ASC
        res_asc = self.client.get(self.global_tasks_url, {'ordering': 'title'})
        self.assertEqual(res_asc.status_code, status.HTTP_200_OK)
        titles_asc = [item['title'] for item in res_asc.data['data']]
        self.assertEqual(titles_asc, sorted(titles_asc))

        # DESC
        res_desc = self.client.get(self.global_tasks_url, {'ordering': '-title'})
        self.assertEqual(res_desc.status_code, status.HTTP_200_OK)
        titles_desc = [item['title'] for item in res_desc.data['data']]
        self.assertEqual(titles_desc, sorted(titles_asc, reverse=True))

    def test_unsafe_ordering_parameter_ignored(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {'ordering': 'created_by'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pagination(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertIsNotNone(response.data['next'])

    def test_invalid_filter_parameter_values(self):
        self.client.force_authenticate(user=self.assignee)
        res_status = self.client.get(self.global_tasks_url, {'status': 'INVALID_STATUS'})
        self.assertEqual(res_status.status_code, status.HTTP_400_BAD_REQUEST)

        res_priority = self.client.get(self.global_tasks_url, {'priority': 'INVALID_PRIORITY'})
        self.assertEqual(res_priority.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtering_does_not_leak_unauthorized_tasks(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {'search': 'Hidden'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_combined_filters(self):
        self.client.force_authenticate(user=self.assignee)
        response = self.client.get(self.global_tasks_url, {
            'project': self.project1.id,
            'status': TaskStatus.TODO,
            'priority': TaskPriority.HIGH
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['data'][0]['task_key'], 'PROJ1-1')
