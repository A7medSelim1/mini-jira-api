from rest_framework import serializers
from apps.comments.models import Comment
from apps.accounts.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment representation and creation.
    """
    author = UserSerializer(read_only=True)
    task_key = serializers.ReadOnlyField(source='task.task_key')

    class Meta:
        model = Comment
        fields = ('id', 'task', 'task_key', 'author', 'content', 'created_at', 'updated_at')
        read_only_fields = ('id', 'task', 'task_key', 'author', 'created_at', 'updated_at')

    def validate_content(self, value):
        content = value.strip() if value else ''
        if not content:
            raise serializers.ValidationError("Comment content cannot be blank.")
        return content
