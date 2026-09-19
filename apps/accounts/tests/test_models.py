from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """
    Unit tests for custom User model.
    """

    def test_create_user_successful(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='Password123!',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('Password123!'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.full_name, 'John Doe')
        self.assertEqual(str(user), 'test@example.com')

    def test_create_user_email_normalized(self):
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='Password123!'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='Password123!')

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)
