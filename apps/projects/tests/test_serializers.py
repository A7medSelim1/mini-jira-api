from django.test import TestCase
from apps.accounts.models import User
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer, ProjectCreateSerializer, ProjectTeamSerializer
from apps.teams.models import Team


class ProjectSerializersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='proj_user@example.com', password='Password123!')
        self.team = Team.objects.create(name='Devs', created_by=self.user)

    def test_project_create_serializer_valid(self):
        data = {'key': 'DEMO', 'title': 'Demo Project', 'description': 'Testing'}
        serializer = ProjectCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['key'], 'DEMO')

    def test_project_create_serializer_duplicate_key_invalid(self):
        Project.objects.create(key='DUPE', title='Original', reporter=self.user)
        data = {'key': 'dupe', 'title': 'Duplicate'}
        serializer = ProjectCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('key', serializer.errors)

    def test_project_create_serializer_non_alphanumeric_key_invalid(self):
        data = {'key': 'PR-10', 'title': 'Bad Key'}
        serializer = ProjectCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('key', serializer.errors)

    def test_project_team_serializer_invalid_team_id(self):
        data = {'team_id': 9999}
        serializer = ProjectTeamSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('team_id', serializer.errors)
