from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership
from apps.teams.services import TeamService


class TeamServiceTest(TestCase):
    """
    Unit tests for TeamService logic.
    """

    def setUp(self):
        self.user = User.objects.create_user(email='leader@example.com', password='Password123!')
        self.member = User.objects.create_user(email='member@example.com', password='Password123!')

    def test_create_team_automatically_adds_creator_membership(self):
        team = TeamService.create_team(name='QA Team', description='Quality Assurance', created_by=self.user)
        self.assertEqual(team.name, 'QA Team')
        self.assertTrue(TeamMembership.objects.filter(team=team, user=self.user).exists())

    def test_add_duplicate_member_raises_validation_error(self):
        team = TeamService.create_team(name='Mobile Team', created_by=self.user)
        with self.assertRaises(ValidationError):
            TeamService.add_member(team=team, user=self.user)

    def test_add_and_remove_member(self):
        team = TeamService.create_team(name='Data Team', created_by=self.user)
        membership = TeamService.add_member(team=team, user=self.member)
        self.assertEqual(membership.user, self.member)

        # Remove member
        result = TeamService.remove_member(team=team, user_id=self.member.id)
        self.assertTrue(result)
        self.assertFalse(TeamMembership.objects.filter(team=team, user=self.member).exists())
