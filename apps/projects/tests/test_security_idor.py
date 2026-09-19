from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership


class ProjectSecurityIDORTest(APITestCase):
    """
    Security test suite verifying IDOR prevention, reporter immutability,
    and server-side project authorization isolation.
    """

    def setUp(self):
        self.reporter1 = User.objects.create_user(email='reporter1@example.com', password='Password123!')
        self.reporter2 = User.objects.create_user(email='reporter2@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project1 = Project.objects.create(key='PROJ1', title='Project One', reporter=self.reporter1)
        self.project2 = Project.objects.create(key='PROJ2', title='Project Two', reporter=self.reporter2)

        self.team1 = Team.objects.create(name='Team 1', created_by=self.reporter1)
        TeamMembership.objects.create(team=self.team1, user=self.reporter1)
        ProjectTeam.objects.create(project=self.project1, team=self.team1)

        self.projects_list_url = reverse('project-list-create')
        self.project1_detail_url = reverse('project-detail', kwargs={'pk': self.project1.id})
        self.project2_detail_url = reverse('project-detail', kwargs={'pk': self.project2.id})

    def test_client_cannot_override_reporter_on_create(self):
        self.client.force_authenticate(user=self.reporter1)
        payload = {
            'key': 'NEWPROJ',
            'title': 'Attempted Hijack',
            'reporter_id': self.reporter2.id  # Trying to set reporter to someone else
        }
        res = self.client.post(self.projects_list_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Server must enforce request.user as reporter
        self.assertEqual(res.data['data']['reporter']['email'], self.reporter1.email)

    def test_client_cannot_change_reporter_via_patch(self):
        self.client.force_authenticate(user=self.reporter1)
        res = self.client.patch(self.project1_detail_url, {'reporter_id': self.reporter2.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.project1.refresh_from_db()
        self.assertEqual(self.project1.reporter, self.reporter1)

    def test_outsider_cannot_retrieve_unauthorized_project_detail(self):
        self.client.force_authenticate(user=self.outsider)
        res = self.client.get(self.project1_detail_url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_reporter_team_member_cannot_update_project(self):
        # Create team member in project 1 who is NOT the reporter
        member = User.objects.create_user(email='member@example.com', password='Password123!')
        TeamMembership.objects.create(team=self.team1, user=member)

        self.client.force_authenticate(user=member)
        res = self.client.patch(self.project1_detail_url, {'title': 'Unauthorized Title Update'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_reporter_cannot_delete_project(self):
        member = User.objects.create_user(email='member2@example.com', password='Password123!')
        TeamMembership.objects.create(team=self.team1, user=member)

        self.client.force_authenticate(user=member)
        res = self.client.delete(self.project1_detail_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_reporter_can_soft_delete_project(self):
        self.client.force_authenticate(user=self.reporter1)
        res = self.client.delete(self.project1_detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.project1.refresh_from_db()
        self.assertTrue(self.project1.is_deleted)
