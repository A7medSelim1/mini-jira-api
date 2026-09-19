from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.projects.services import ProjectService
from apps.tasks.services import TaskService
from apps.comments.services import CommentService
from apps.tasks.models import TaskStatus
from apps.activities.models import ActivityAction


class ActivityViewsTest(APITestCase):
    """
    API integration tests for Activity/Audit History read-only endpoints and IDOR protection.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.member = User.objects.create_user(email='member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        # Create Project & Team
        self.project = ProjectService.create_project(
            key='AUDIT',
            title='Audit Project',
            reporter=self.reporter
        )
        self.team = Team.objects.create(name='Audit Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.member)
        ProjectService.assign_team(self.project, self.team, self.reporter)

        # Create Task
        self.task = TaskService.create_task(
            project=self.project,
            title='Audit Task',
            created_by=self.reporter,
            assignee=self.member
        )

        # Add comment & state transition
        self.comment = CommentService.add_comment(self.task, self.member, 'Test comment for audit')
        TaskService.transition_task(self.task.id, TaskStatus.IN_PROGRESS, self.member)

        self.project_activities_url = reverse('project-activities-list', kwargs={'project_id': self.project.id})
        self.task_activities_url = reverse('task-activities-list', kwargs={'task_id': self.task.id})

    def test_list_project_activities_authenticated(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.project_activities_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify recorded actions exist in response data
        actions = [item['action'] for item in response.data['data']]
        self.assertIn(ActivityAction.PROJECT_CREATED, actions)
        self.assertIn(ActivityAction.TASK_CREATED, actions)
        self.assertIn(ActivityAction.COMMENT_ADDED, actions)
        self.assertIn(ActivityAction.TASK_STATUS_CHANGED, actions)

    def test_list_task_activities_authenticated(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.task_activities_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        actions = [item['action'] for item in response.data['data']]
        self.assertIn(ActivityAction.TASK_CREATED, actions)
        self.assertIn(ActivityAction.TASK_STATUS_CHANGED, actions)

    def test_outsider_cannot_access_project_activities(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.project_activities_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_access_task_activities(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.task_activities_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
