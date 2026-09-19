from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership


class TeamViewsTest(APITestCase):
    """
    API integration tests for Team views.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(email='owner@example.com', password='Password123!')
        self.user2 = User.objects.create_user(email='other@example.com', password='Password123!')

        self.team = Team.objects.create(name='Core Team', created_by=self.user1)
        TeamMembership.objects.create(team=self.team, user=self.user1)

        self.list_create_url = reverse('team-list-create')
        self.detail_url = reverse('team-detail', kwargs={'pk': self.team.id})
        self.members_url = reverse('team-members-list-create', kwargs={'pk': self.team.id})

    def test_list_teams_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)

    def test_create_team_api(self):
        self.client.force_authenticate(user=self.user1)
        payload = {'name': 'New Product Team', 'description': 'Building next-gen platform'}
        response = self.client.post(self.list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'New Product Team')

    def test_add_team_member_api(self):
        self.client.force_authenticate(user=self.user1)
        payload = {'email': self.user2.email}
        response = self.client.post(self.members_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

    def test_non_member_cannot_access_team_detail(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
