from rest_framework import serializers
from apps.tasks.models import TaskStatus


class TaskTransitionSerializer(serializers.Serializer):
    """
    Serializer for validating Task status transition payload.
    """
    status = serializers.ChoiceField(choices=TaskStatus.choices)
