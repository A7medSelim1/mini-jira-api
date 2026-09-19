from django.test import TestCase
from django.db.utils import IntegrityError
from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership


class TeamModelsTest(TestCase):
    """
    Unit tests for Team and TeamMembership models.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='Password123!')
        self.user2 = User.objects.create_user(email='user2@example.com', password='Password123!')

    def test_create_team(self):
        team = Team.objects.create(name='Backend Team', description='Backend devs', created_by=self.user1)
        self.assertEqual(team.name, 'Backend Team')
        self.assertEqual(team.created_by, self.user1)
        self.assertEqual(str(team), 'Backend Team')

    def test_unique_team_name_constraint(self):
        Team.objects.create(name='Frontend Team', created_by=self.user1)
        with self.assertRaises(IntegrityError):
            Team.objects.create(name='Frontend Team', created_by=self.user2)

    def test_unique_team_membership_constraint(self):
        team = Team.objects.create(name='DevOps Team', created_by=self.user1)
        TeamMembership.objects.create(team=team, user=self.user1)
        with self.assertRaises(IntegrityError):
            TeamMembership.objects.create(team=team, user=self.user1)
