from rest_framework import serializers
from apps.tasks.models import TaskPriority
from apps.accounts.models import User
from apps.teams.models import TeamMembership


class TaskCreateSerializer(serializers.Serializer):
    """
    Serializer for validating Task creation input payload.
    Validates that assignee is eligible for the task's project.
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    priority = serializers.ChoiceField(choices=TaskPriority.choices, default=TaskPriority.MEDIUM)
    assignee_id = serializers.IntegerField(required=False, allow_null=True, default=None)

    def validate_title(self, value):
        title = value.strip() if value else ''
        if not title:
            raise serializers.ValidationError("Task title cannot be blank.")
        return title

    def validate_assignee_id(self, value):
        if value is None:
            return None

        project = self.context.get('project')
        assignee = User.objects.filter(id=value, is_active=True).first()
        if not assignee:
            raise serializers.ValidationError("Assignee user does not exist or is inactive.")

        if project:
            is_reporter = (project.reporter_id == assignee.id)
            is_team_member = TeamMembership.objects.filter(
                user=assignee,
                team__project_teams__project=project
            ).exists()

            if not is_reporter and not is_team_member:
                raise serializers.ValidationError("Assignee must belong to a team assigned to this project.")

        return value
