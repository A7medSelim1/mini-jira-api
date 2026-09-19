from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, TaskStatus, TaskPriority


class TaskWorkflowTest(APITestCase):
    """
    Exhaustive verification of Task status workflow state machine transitions,
    actor authorization rules, invalid transition handling, and PATCH status bypass blocking.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.assignee = User.objects.create_user(email='assignee@example.com', password='Password123!')
        self.team_member = User.objects.create_user(email='member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(key='FLOW', title='Workflow Project', reporter=self.reporter)
        self.team = Team.objects.create(name='Workflow Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.assignee)
        TeamMembership.objects.create(team=self.team, user=self.team_member)
        ProjectTeam.objects.create(project=self.project, team=self.team)

    def test_valid_transition_todo_to_in_progress_by_assignee(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.TODO
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.assignee)
        res = self.client.post(url, {'status': TaskStatus.IN_PROGRESS}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['status'], TaskStatus.IN_PROGRESS)

    def test_valid_transition_in_progress_to_ready_for_review_by_assignee(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.IN_PROGRESS
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.assignee)
        res = self.client.post(url, {'status': TaskStatus.READY_FOR_REVIEW}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['status'], TaskStatus.READY_FOR_REVIEW)

    def test_valid_transition_ready_for_review_to_done_by_reporter(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.READY_FOR_REVIEW
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.reporter)
        res = self.client.post(url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['status'], TaskStatus.DONE)

    def test_valid_transition_ready_for_review_to_todo_rejection_by_reporter(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.READY_FOR_REVIEW
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.reporter)
        res = self.client.post(url, {'status': TaskStatus.TODO}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['status'], TaskStatus.TODO)

    def test_assignee_cannot_approve_task_to_done(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.READY_FOR_REVIEW
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.assignee)
        res = self.client.post(url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_assignee_team_member_cannot_start_task(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.TODO
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.team_member)
        res = self.client.post(url, {'status': TaskStatus.IN_PROGRESS}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_direct_transition_todo_to_done(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.TODO
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.reporter)
        res = self.client.post(url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_direct_transition_todo_to_ready_for_review(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.TODO
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.assignee)
        res = self.client.post(url, {'status': TaskStatus.READY_FOR_REVIEW}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_direct_transition_in_progress_to_done(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.IN_PROGRESS
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.reporter)
        res = self.client.post(url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_transition_from_done_to_any_status(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.DONE
        )
        url = reverse('task-transition', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.reporter)
        for target in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.READY_FOR_REVIEW]:
            res = self.client.post(url, {'status': target}, format='json')
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_attempt_status_change_via_patch_returns_bad_request(self):
        task = Task.objects.create(
            task_key='FLOW-1', sequence_number=1, title='Task 1',
            project=self.project, created_by=self.reporter, assignee=self.assignee,
            status=TaskStatus.TODO
        )
        detail_url = reverse('task-detail', kwargs={'pk': task.id})
        self.client.force_authenticate(user=self.reporter)
        res = self.client.patch(detail_url, {'status': TaskStatus.DONE}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('PATCH', res.data['error']['message'])
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.TODO)
