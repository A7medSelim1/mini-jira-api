from rest_framework import serializers
from apps.activities.models import ActivityLog
from apps.accounts.serializers import UserSerializer


class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for ActivityLog audit entries.
    """
    actor = UserSerializer(read_only=True)
    project_key = serializers.ReadOnlyField(source='project.key')
    task_key = serializers.ReadOnlyField(source='task.task_key', default=None)

    class Meta:
        model = ActivityLog
        fields = (
            'id', 'project', 'project_key', 'task', 'task_key',
            'actor', 'action', 'metadata', 'timestamp'
        )
        read_only_fields = (
            'id', 'project', 'project_key', 'task', 'task_key',
            'actor', 'action', 'metadata', 'timestamp'
        )
