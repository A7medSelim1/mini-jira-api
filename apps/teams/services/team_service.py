from django.db import transaction
from django.core.exceptions import ValidationError
from apps.teams.models import Team, TeamMembership
from apps.accounts.models import User


class TeamService:
    """
    Business logic operations for Teams and TeamMemberships.
    """

    @staticmethod
    @transaction.atomic
    def create_team(name: str, description: str = '', created_by: User = None) -> Team:
        """
        Creates a new team and automatically adds the creator as a team member.
        """
        name = name.strip()
        if Team.objects.filter(name=name).exists():
            raise ValidationError({'name': 'A team with this name already exists.'})

        team = Team.objects.create(
            name=name,
            description=description,
            created_by=created_by
        )

        if created_by:
            TeamMembership.objects.get_or_create(
                team=team,
                user=created_by
            )

        return team

    @staticmethod
    @transaction.atomic
    def add_member(team: Team, user: User) -> TeamMembership:
        """
        Adds a user to a team. Prevents duplicate membership.
        """
        membership, created = TeamMembership.objects.get_or_create(
            team=team,
            user=user
        )
        if not created:
            raise ValidationError({'user': 'User is already a member of this team.'})
        return membership

    @staticmethod
    @transaction.atomic
    def remove_member(team: Team, user_id: int) -> bool:
        """
        Removes a user from a team.
        """
        deleted_count, _ = TeamMembership.objects.filter(
            team=team,
            user_id=user_id
        ).delete()
        
        if deleted_count == 0:
            raise ValidationError({'user': 'User is not a member of this team.'})
        return True

    @staticmethod
    @transaction.atomic
    def update_team(team: Team, name: str = None, description: str = None) -> Team:
        """
        Updates team details.
        """
        if name is not None:
            name = name.strip()
            if Team.objects.filter(name=name).exclude(id=team.id).exists():
                raise ValidationError({'name': 'A team with this name already exists.'})
            team.name = name
        if description is not None:
            team.description = description
        team.save()
        return team

    @staticmethod
    @transaction.atomic
    def delete_team(team: Team) -> None:
        """
        Deletes a team.
        """
        team.delete()
