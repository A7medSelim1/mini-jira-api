from django.test import TestCase
from django.db.utils import IntegrityError
from apps.accounts.models import User
from apps.teams.models import Team
from apps.projects.models import Project, ProjectTeam


class ProjectModelsTest(TestCase):
    """
    Unit tests for Project and ProjectTeam models.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.team = Team.objects.create(name='Dev Team', created_by=self.reporter)

    def test_create_project(self):
        project = Project.objects.create(
            key='PROJ',
            title='Core Platform',
            description='Main product',
            reporter=self.reporter
        )
        self.assertEqual(project.key, 'PROJ')
        self.assertEqual(str(project), '[PROJ] Core Platform')
        self.assertFalse(project.is_deleted)

    def test_project_key_auto_uppercase(self):
        project = Project.objects.create(
            key='proj',
            title='Auto Upper',
            reporter=self.reporter
        )
        self.assertEqual(project.key, 'PROJ')

    def test_unique_project_key_constraint(self):
        Project.objects.create(key='ALPHA', title='First', reporter=self.reporter)
        with self.assertRaises(IntegrityError):
            Project.objects.create(key='ALPHA', title='Second', reporter=self.reporter)

    def test_project_team_unique_constraint(self):
        project = Project.objects.create(key='BETA', title='Beta Project', reporter=self.reporter)
        ProjectTeam.objects.create(project=project, team=self.team)
        with self.assertRaises(IntegrityError):
            ProjectTeam.objects.create(project=project, team=self.team)

    def test_active_manager_filters_soft_deleted(self):
        p1 = Project.objects.create(key='P1', title='P1', reporter=self.reporter)
        p2 = Project.objects.create(key='P2', title='P2', reporter=self.reporter)
        p2.is_deleted = True
        p2.save()

        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.all_objects.count(), 2)
