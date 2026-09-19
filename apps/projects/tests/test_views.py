from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership


class ProjectViewsTest(APITestCase):
    """
    API integration tests for Project endpoints.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.member = User.objects.create_user(email='member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.team = Team.objects.create(name='Project Dev Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.member)

        self.list_create_url = reverse('project-list-create')

    def test_create_project_api_success(self):
        self.client.force_authenticate(user=self.reporter)
        payload = {
            'key': 'ALPHA',
            'title': 'Alpha Project',
            'description': 'Description'
        }
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['key'], 'ALPHA')
        self.assertEqual(response.data['data']['reporter']['email'], self.reporter.email)

    def test_create_project_invalid_key_fails(self):
        self.client.force_authenticate(user=self.reporter)
        payload = {'key': 'AL-10', 'title': 'Bad Key Project'}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_list_accessible_projects_api(self):
        # Reporter creates project
        p1 = Project.objects.create(key='P1', title='Project 1', reporter=self.reporter)
        ProjectTeam.objects.create(project=p1, team=self.team)

        # Outsider project
        Project.objects.create(key='SECRET', title='Secret Project', reporter=self.outsider)

        # Assigned team member lists projects
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['key'], 'P1')

    def test_retrieve_project_unauthorized_fails(self):
        project = Project.objects.create(key='PRIV', title='Private', reporter=self.reporter)
        url = reverse('project-detail', kwargs={'pk': project.id})

        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_project_by_reporter_success(self):
        project = Project.objects.create(key='UPD', title='Old Title', reporter=self.reporter)
        url = reverse('project-detail', kwargs={'pk': project.id})

        self.client.force_authenticate(user=self.reporter)
        response = self.client.patch(url, {'title': 'New Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], 'New Title')

    def test_update_project_by_non_reporter_forbidden(self):
        project = Project.objects.create(key='UPD2', title='Title', reporter=self.reporter)
        ProjectTeam.objects.create(project=project, team=self.team)
        url = reverse('project-detail', kwargs={'pk': project.id})

        self.client.force_authenticate(user=self.member)
        response = self.client.patch(url, {'title': 'Hacked Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete_project_api(self):
        project = Project.objects.create(key='DEL', title='To Delete', reporter=self.reporter)
        url = reverse('project-detail', kwargs={'pk': project.id})

        self.client.force_authenticate(user=self.reporter)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Project.all_objects.get(id=project.id).is_deleted)
        self.assertEqual(Project.objects.count(), 0)

    def test_assign_and_remove_team_api(self):
        project = Project.objects.create(key='TEAM', title='Team Project', reporter=self.reporter)
        teams_url = reverse('project-teams-list-create', kwargs={'pk': project.id})

        self.client.force_authenticate(user=self.reporter)
        assign_res = self.client.post(teams_url, {'team_id': self.team.id}, format='json')
        self.assertEqual(assign_res.status_code, status.HTTP_201_CREATED)

        remove_url = reverse('project-teams-detail', kwargs={'pk': project.id, 'team_id': self.team.id})
        remove_res = self.client.delete(remove_url)
        self.assertEqual(remove_res.status_code, status.HTTP_200_OK)
