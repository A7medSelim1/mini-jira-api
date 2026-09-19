from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.projects.models import Project, ProjectTeam
from apps.teams.models import Team
from apps.activities.models import ActivityLog, ActivityAction
from apps.accounts.models import User


class ProjectService:
    """
    Service layer for Project operations and atomic activity logging.
    """

    @staticmethod
    @transaction.atomic
    def create_project(key: str, title: str, description: str = '', reporter: User = None) -> Project:
        """
        Creates a new project and logs initial creation activity.
        """
        key = key.strip().upper()
        if Project.all_objects.filter(key=key).exists():
            raise ValidationError({'key': 'A project with this key already exists.'})

        project = Project.objects.create(
            key=key,
            title=title.strip(),
            description=description,
            reporter=reporter
        )

        ActivityLog.objects.create(
            project=project,
            actor=reporter,
            action=ActivityAction.PROJECT_CREATED,
            metadata={'key': project.key, 'title': project.title}
        )

        return project

    @staticmethod
    @transaction.atomic
    def assign_team(project: Project, team: Team, actor: User) -> ProjectTeam:
        """
        Assigns a team to a project. Prevents duplicate assignment.
        """
        assignment, created = ProjectTeam.objects.get_or_create(
            project=project,
            team=team
        )
        if not created:
            raise ValidationError({'team': 'Team is already assigned to this project.'})

        ActivityLog.objects.create(
            project=project,
            actor=actor,
            action=ActivityAction.PROJECT_TEAM_ADDED,
            metadata={'team_id': team.id, 'team_name': team.name}
        )

        return assignment

    @staticmethod
    @transaction.atomic
    def remove_team(project: Project, team_id: int, actor: User) -> bool:
        """
        Removes a team from a project.
        """
        assignment = ProjectTeam.objects.filter(project=project, team_id=team_id).first()
        if not assignment:
            raise ValidationError({'team': 'Team is not assigned to this project.'})

        team_name = assignment.team.name
        assignment.delete()

        ActivityLog.objects.create(
            project=project,
            actor=actor,
            action=ActivityAction.PROJECT_TEAM_REMOVED,
            metadata={'team_id': team_id, 'team_name': team_name}
        )

        return True

    @staticmethod
    @transaction.atomic
    def soft_delete_project(project: Project, actor: User) -> None:
        """
        Soft deletes a project.
        """
        project.is_deleted = True
        project.deleted_at = timezone.now()
        project.save()
