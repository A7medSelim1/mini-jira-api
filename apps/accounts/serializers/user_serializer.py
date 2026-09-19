from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User representation and profile updates.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'date_joined')
        read_only_fields = ('id', 'email', 'date_joined')

    @extend_schema_field(serializers.CharField)
    def get_full_name(self, obj) -> str:
        return obj.full_name

