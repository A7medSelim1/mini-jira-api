from rest_framework import serializers
from apps.teams.models import TeamMembership
from apps.accounts.serializers import UserSerializer


class TeamMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for Team membership representation.
    """
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = TeamMembership
        fields = ('id', 'team', 'user', 'user_id', 'joined_at')
        read_only_fields = ('id', 'team', 'user', 'joined_at')
