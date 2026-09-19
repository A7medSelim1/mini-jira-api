from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.comments.serializers import CommentSerializer
from apps.comments.selectors import CommentSelector
from apps.comments.services import CommentService
from apps.tasks.selectors import TaskSelector


class CommentListCreateView(APIView):
    """
    GET /api/v1/tasks/{task_id}/comments/ - List comments for a task.
    POST /api/v1/tasks/{task_id}/comments/ - Add a comment to a task.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CommentSerializer

    @extend_schema(
        responses={200: CommentSerializer(many=True)},
        summary="List Task Comments",
        description="Fetch all active comments associated with the specified task."
    )
    def get(self, request, task_id: int, *args, **kwargs):
        task = TaskSelector.get_task_by_id(task_id, request.user)
        if not task:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Task not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        comments = CommentSelector.get_task_comments(task.id, request.user)
        serializer = CommentSerializer(comments, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=CommentSerializer,
        responses={201: CommentSerializer},
        summary="Add Task Comment",
        description="Add a new comment to the specified task. Author automatically set to request.user."
    )
    def post(self, request, task_id: int, *args, **kwargs):
        task = TaskSelector.get_task_by_id(task_id, request.user)
        if not task:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Task not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = CommentService.add_comment(
                task=task,
                author=request.user,
                content=serializer.validated_data['content']
            )
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Failed to add comment.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Comment added successfully.",
            "data": CommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)
