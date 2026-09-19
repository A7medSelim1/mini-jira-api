from rest_framework import serializers
from apps.teams.models import Team
from apps.accounts.serializers import UserSerializer


class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer for Team list, detail, and creation operations.
    """
    created_by = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'created_by', 'member_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'member_count', 'created_at', 'updated_at')
