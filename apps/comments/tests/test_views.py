from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task
from apps.comments.models import Comment


class CommentViewsTest(APITestCase):
    """
    API integration tests for Comment endpoints.
    """

    def setUp(self):
        self.reporter = User.objects.create_user(email='reporter@example.com', password='Password123!')
        self.author = User.objects.create_user(email='author@example.com', password='Password123!')
        self.other_member = User.objects.create_user(email='other_member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(key='COMM', title='Comment Project', reporter=self.reporter)
        self.team = Team.objects.create(name='Comment Team', created_by=self.reporter)
        TeamMembership.objects.create(team=self.team, user=self.author)
        TeamMembership.objects.create(team=self.team, user=self.other_member)
        ProjectTeam.objects.create(project=self.project, team=self.team)

        self.task = Task.objects.create(
            task_key='COMM-1',
            sequence_number=1,
            title='Comment Task',
            project=self.project,
            created_by=self.reporter
        )

        self.task_comments_url = reverse('task-comments-list-create', kwargs={'task_id': self.task.id})

    def test_create_comment_api_success(self):
        self.client.force_authenticate(user=self.author)
        payload = {'content': 'Initial feedback on task'}
        response = self.client.post(self.task_comments_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['author']['email'], self.author.email)

    def test_list_comments_api(self):
        Comment.objects.create(task=self.task, author=self.author, content='Comment 1')
        Comment.objects.create(task=self.task, author=self.other_member, content='Comment 2')

        self.client.force_authenticate(user=self.author)
        response = self.client.get(self.task_comments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_unauthorized_task_access_rejected(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(self.task_comments_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_own_comment_success(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='Original')
        detail_url = reverse('comment-detail', kwargs={'pk': comment.id})

        self.client.force_authenticate(user=self.author)
        response = self.client.patch(detail_url, {'content': 'Updated content'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['content'], 'Updated content')

    def test_edit_another_users_comment_forbidden(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='Original')
        detail_url = reverse('comment-detail', kwargs={'pk': comment.id})

        self.client.force_authenticate(user=self.other_member)
        response = self.client.patch(detail_url, {'content': 'Hacked content'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_comment_success(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='To delete')
        detail_url = reverse('comment-detail', kwargs={'pk': comment.id})

        self.client.force_authenticate(user=self.author)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Comment.all_objects.get(id=comment.id).is_deleted)

    def test_delete_another_users_comment_by_non_reporter_forbidden(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='Author comment')
        detail_url = reverse('comment-detail', kwargs={'pk': comment.id})

        self.client.force_authenticate(user=self.other_member)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_another_users_comment_by_reporter_allowed(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='Author comment')
        detail_url = reverse('comment-detail', kwargs={'pk': comment.id})

        # Reporter moderation delete
        self.client.force_authenticate(user=self.reporter)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Comment.all_objects.get(id=comment.id).is_deleted)
