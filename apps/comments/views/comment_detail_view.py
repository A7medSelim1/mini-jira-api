from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from apps.comments.serializers import CommentSerializer
from apps.comments.models import Comment
from apps.comments.services import CommentService
from apps.comments.permissions import IsCommentAuthor, IsCommentAuthorOrReporter
from apps.tasks.selectors import TaskSelector


class CommentDetailView(APIView):
    """
    GET /api/v1/comments/{id}/ - Retrieve comment detail.
    PATCH /api/v1/comments/{id}/ - Edit own comment.
    DELETE /api/v1/comments/{id}/ - Delete own comment or moderation delete by Reporter.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CommentSerializer

    def get_comment(self, comment_id: int) -> Comment | None:
        try:
            comment = Comment.objects.select_related('author', 'task__project').get(id=comment_id)
            # Verify project access
            if TaskSelector.get_task_by_id(comment.task_id, self.request.user):
                return comment
            return None
        except Comment.DoesNotExist:
            return None

    @extend_schema(
        responses={200: CommentSerializer},
        summary="Retrieve Comment Details",
        description="Fetch detailed comment information."
    )
    def get(self, request, pk: int, *args, **kwargs):
        comment = self.get_comment(pk)
        if not comment:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Comment not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "data": CommentSerializer(comment).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=CommentSerializer,
        responses={200: CommentSerializer},
        summary="Update Comment Content",
        description="Update comment text. Only comment author is allowed."
    )
    def patch(self, request, pk: int, *args, **kwargs):
        self.permission_classes = (permissions.IsAuthenticated, IsCommentAuthor)
        comment = self.get_comment(pk)
        if not comment:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Comment not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, comment)

        serializer = CommentSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if 'content' in serializer.validated_data:
            comment.content = serializer.validated_data['content']
            comment.save()

        return Response({
            "success": True,
            "message": "Comment updated successfully.",
            "data": CommentSerializer(comment).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Soft-Delete Comment",
        description="Soft-delete a comment. Requires comment author permission or Project Reporter moderation permission."
    )
    def delete(self, request, pk: int, *args, **kwargs):
        self.permission_classes = (permissions.IsAuthenticated, IsCommentAuthorOrReporter)
        comment = self.get_comment(pk)
        if not comment:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Comment not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, comment)

        CommentService.soft_delete_comment(comment, request.user)

        return Response({
            "success": True,
            "message": "Comment deleted successfully."
        }, status=status.HTTP_200_OK)
