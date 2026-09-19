from rest_framework import serializers
from apps.projects.models import Project


class ProjectCreateSerializer(serializers.Serializer):
    """
    Serializer for validating Project creation payload.
    """
    key = serializers.CharField(max_length=10)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_key(self, value):
        key = value.strip().upper() if value else ''
        if not key.isalnum():
            raise serializers.ValidationError("Project key must contain only letters and numbers.")
        if Project.all_objects.filter(key=key).exists():
            raise serializers.ValidationError("A project with this key already exists.")
        return key

    def validate_title(self, value):
        title = value.strip() if value else ''
        if not title:
            raise serializers.ValidationError("Project title cannot be blank.")
        return title
