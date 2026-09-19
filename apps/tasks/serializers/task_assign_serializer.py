from rest_framework import serializers
from apps.accounts.models import User
from apps.teams.models import TeamMembership


class TaskAssignSerializer(serializers.Serializer):
    """
    Serializer for validating Task assignment payload.
    Ensures assignee is eligible for the project.
    """
    assignee_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_assignee_id(self, value):
        if value is None:
            return None

        project = self.context.get('project')
        task = self.context.get('task')
        if not project and task:
            project = task.project

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
