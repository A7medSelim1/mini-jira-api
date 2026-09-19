from django.test import TestCase
from apps.accounts.services import AuthService
from apps.accounts.models import User


class AuthServiceTest(TestCase):
    """
    Unit tests for AuthService.
    """

    def test_register_user_service(self):
        user = AuthService.register_user(
            email='service_user@example.com',
            password='Password123!',
            first_name='Alice',
            last_name='Smith'
        )
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, 'service_user@example.com')
        self.assertEqual(user.first_name, 'Alice')

    def test_update_profile_service(self):
        user = AuthService.register_user(
            email='profile@example.com',
            password='Password123!',
            first_name='Bob'
        )
        updated_user = AuthService.update_profile(
            user=user,
            first_name='Robert',
            last_name='Johnson'
        )
        self.assertEqual(updated_user.first_name, 'Robert')
        self.assertEqual(updated_user.last_name, 'Johnson')
