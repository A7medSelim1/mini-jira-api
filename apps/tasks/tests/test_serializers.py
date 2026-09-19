from django.test import TestCase
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import TaskPriority, TaskStatus
from apps.tasks.serializers import TaskCreateSerializer, TaskAssignSerializer, TaskTransitionSerializer


class TaskSerializersTest(TestCase):
    def setUp(self):
        self.reporter = User.objects.create_user(email='rep@example.com', password='Password123!')
        self.team_member = User.objects.create_user(email='member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(key='TASK', title='Task Project', reporter=self.reporter)
        self.team = Team.objects.create(name='Task Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.team_member)
        ProjectTeam.objects.create(project=self.project, team=self.team)

    def test_task_create_serializer_valid_eligible_assignee(self):
        data = {
            'title': 'Build Feature',
            'description': 'Feature details',
            'priority': TaskPriority.HIGH,
            'assignee_id': self.team_member.id
        }
        serializer = TaskCreateSerializer(data=data, context={'project': self.project})
        self.assertTrue(serializer.is_valid())

    def test_task_create_serializer_ineligible_assignee_invalid(self):
        data = {
            'title': 'Build Feature',
            'priority': TaskPriority.LOW,
            'assignee_id': self.outsider.id
        }
        serializer = TaskCreateSerializer(data=data, context={'project': self.project})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignee_id', serializer.errors)

    def test_task_transition_serializer_valid(self):
        data = {'status': TaskStatus.IN_PROGRESS}
        serializer = TaskTransitionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_task_transition_serializer_invalid_choice(self):
        data = {'status': 'INVALID_STATUS'}
        serializer = TaskTransitionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
