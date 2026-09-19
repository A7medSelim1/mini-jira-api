from rest_framework import serializers
from apps.projects.models import ProjectTeam
from apps.teams.models import Team
from apps.teams.serializers import TeamSerializer


class ProjectTeamSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectTeam assignments.
    """
    team = TeamSerializer(read_only=True)
    team_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProjectTeam
        fields = ('id', 'project', 'team', 'team_id', 'assigned_at')
        read_only_fields = ('id', 'project', 'team', 'assigned_at')

    def validate_team_id(self, value):
        if not Team.objects.filter(id=value).exists():
            raise serializers.ValidationError("Team not found.")
        return value
