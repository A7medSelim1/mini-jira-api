from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.teams.models import Team, TeamMembership
from apps.projects.models import Project, ProjectTeam
from apps.tasks.services import TaskService


class TeamProjectAssignmentTest(APITestCase):
    """
    Integration tests covering Team management, Project-Team assignment,
    duplicate prevention, authorization boundaries, and task assignee eligibility.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='project_owner@example.com', password='Password123!')
        self.team_creator = User.objects.create_user(email='team_creator@example.com', password='Password123!')
        self.member = User.objects.create_user(email='team_member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='unrelated_user@example.com', password='Password123!')

        # Create Project & Team
        self.project = Project.objects.create(key='TEAMPRJ', title='Team Project', reporter=self.reporter)
        self.team = Team.objects.create(name='Alpha Devs', created_by=self.team_creator)
        TeamMembership.objects.create(team=self.team, user=self.team_creator)

        self.teams_url = reverse('team-list-create')
        self.team_detail_url = reverse('team-detail', kwargs={'pk': self.team.id})
        self.team_members_url = reverse('team-members-list-create', kwargs={'pk': self.team.id})
        self.project_teams_url = reverse('project-teams-list-create', kwargs={'pk': self.project.id})

    def test_team_creation_success(self):
        self.client.force_authenticate(user=self.team_creator)
        payload = {'name': 'Beta DevOps', 'description': 'DevOps engineers'}
        response = self.client.post(self.teams_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Beta DevOps')

    def test_member_management_add_and_remove(self):
        self.client.force_authenticate(user=self.team_creator)
        
        # Add member
        add_res = self.client.post(self.team_members_url, {'email': self.member.email}, format='json')
        self.assertEqual(add_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(TeamMembership.objects.filter(team=self.team, user=self.member).exists())

        # Remove member
        remove_url = reverse('team-members-detail', kwargs={'pk': self.team.id, 'user_id': self.member.id})
        remove_res = self.client.delete(remove_url)
        self.assertEqual(remove_res.status_code, status.HTTP_200_OK)
        self.assertFalse(TeamMembership.objects.filter(team=self.team, user=self.member).exists())

    def test_duplicate_membership_prevention_fails(self):
        self.client.force_authenticate(user=self.team_creator)
        # Attempt to add team_creator again
        response = self.client.post(self.team_members_url, {'email': self.team_creator.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_project_team_assignment_and_duplicate_prevention(self):
        self.client.force_authenticate(user=self.reporter)

        # Assign team to project
        assign_res = self.client.post(self.project_teams_url, {'team_id': self.team.id}, format='json')
        self.assertEqual(assign_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProjectTeam.objects.filter(project=self.project, team=self.team).exists())

        # Attempt duplicate assignment
        dupe_res = self.client.post(self.project_teams_url, {'team_id': self.team.id}, format='json')
        self.assertEqual(dupe_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_team_modification_forbidden(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.patch(self.team_detail_url, {'name': 'Hacked Team'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_project_team_modification_forbidden(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(self.project_teams_url, {'team_id': self.team.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_assignee_eligibility(self):
        # 1. Outsider is initially NOT eligible for project tasks
        self.assertFalse(TaskService.is_assignee_eligible(self.project, self.outsider))

        # 2. Member of team is NOT eligible until team is assigned to project
        self.assertFalse(TaskService.is_assignee_eligible(self.project, self.member))

        # Assign team to project
        ProjectTeam.objects.create(project=self.project, team=self.team)
        TeamMembership.objects.create(team=self.team, user=self.member)

        # 3. Now team member IS eligible for project tasks
        self.assertTrue(TaskService.is_assignee_eligible(self.project, self.member))

        # 4. Project reporter is ALWAYS eligible for project tasks
        self.assertTrue(TaskService.is_assignee_eligible(self.project, self.reporter))
