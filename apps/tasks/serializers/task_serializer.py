from rest_framework import serializers
from apps.tasks.models import Task
from apps.accounts.serializers import UserSerializer


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task detail representation.
    """
    created_by = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    project_key = serializers.ReadOnlyField(source='project.key')

    class Meta:
        model = Task
        fields = (
            'id', 'task_key', 'sequence_number', 'title', 'description',
            'project', 'project_key', 'created_by', 'assignee',
            'status', 'priority', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'task_key', 'sequence_number', 'project', 'project_key',
            'created_by', 'assignee', 'status', 'created_at', 'updated_at'
        )

    def validate_title(self, value):
        title = value.strip() if value else ''
        if not title:
            raise serializers.ValidationError("Task title cannot be blank.")
        return title
