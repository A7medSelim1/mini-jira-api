from django.test import TestCase
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.projects.permissions import HasProjectAccess, IsProjectReporter
from apps.projects.selectors import ProjectSelector


class ProjectPermissionsTest(TestCase):
    def setUp(self):
        self.reporter = User.objects.create_user(email='rep@example.com', password='Password123!')
        self.member = User.objects.create_user(email='mem@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='out@example.com', password='Password123!')

        self.project = Project.objects.create(key='PERM', title='Perm Project', reporter=self.reporter)
        self.team = Team.objects.create(name='Perm Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.member)
        ProjectTeam.objects.create(project=self.project, team=self.team)

        self.access_perm = HasProjectAccess()
        self.reporter_perm = IsProjectReporter()

    def test_reporter_has_project_access(self):
        self.assertTrue(self.access_perm.has_object_permission(
            type('Req', (), {'user': self.reporter}), None, self.project
        ))

    def test_team_member_has_project_access(self):
        self.assertTrue(self.access_perm.has_object_permission(
            type('Req', (), {'user': self.member}), None, self.project
        ))

    def test_outsider_denied_project_access(self):
        self.assertFalse(self.access_perm.has_object_permission(
            type('Req', (), {'user': self.outsider}), None, self.project
        ))

    def test_project_selector_idor_protection(self):
        # Reporter sees project
        self.assertIsNotNone(ProjectSelector.get_project_by_id(self.project.id, self.reporter))
        # Assigned team member sees project
        self.assertIsNotNone(ProjectSelector.get_project_by_id(self.project.id, self.member))
        # Outsider gets None (IDOR protected)
        self.assertIsNone(ProjectSelector.get_project_by_id(self.project.id, self.outsider))
