from rest_framework import serializers
from apps.projects.models import Project
from apps.accounts.serializers import UserSerializer


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project representation and detail view.
    """
    reporter = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'key', 'title', 'description', 'reporter', 'created_at', 'updated_at')
        read_only_fields = ('id', 'key', 'reporter', 'created_at', 'updated_at')

    def validate_title(self, value):
        title = value.strip() if value else ''
        if not title:
            raise serializers.ValidationError("Project title cannot be blank.")
        return title
