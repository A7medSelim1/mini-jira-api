from django.db import transaction
from apps.accounts.models import User


class AuthService:
    """
    Business logic service for User Authentication and Profile Management.
    """

    @staticmethod
    @transaction.atomic
    def register_user(email: str, password: str, first_name: str = '', last_name: str = '') -> User:
        """
        Creates a new user with normalized email and hashed password.
        """
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        return user

    @staticmethod
    @transaction.atomic
    def update_profile(user: User, first_name: str = None, last_name: str = None) -> User:
        """
        Updates user profile details.
        """
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        user.save()
        return user
