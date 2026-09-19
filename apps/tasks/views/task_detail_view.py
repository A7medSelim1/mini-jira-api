from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from apps.tasks.serializers import TaskSerializer
from apps.tasks.selectors import TaskSelector
from apps.tasks.permissions import HasTaskAccess
from apps.activities.models import ActivityLog, ActivityAction


class TaskDetailView(APIView):
    """
    GET /api/v1/tasks/{id}/ - Retrieve task details.
    PATCH /api/v1/tasks/{id}/ - Update task title/description/priority (status excluded).
    DELETE /api/v1/tasks/{id}/ - Soft delete task.
    """
    permission_classes = (permissions.IsAuthenticated, HasTaskAccess)
    serializer_class = TaskSerializer

    def get_object(self, task_id: int):
        task = TaskSelector.get_task_by_id(task_id, self.request.user)
        if not task:
            return None
        self.check_object_permissions(self.request, task)
        return task

    @extend_schema(
        responses={200: TaskSerializer},
        summary="Retrieve Task Details",
        description="Fetch detailed task information."
    )
    def get(self, request, pk: int, *args, **kwargs):
        task = self.get_object(pk)
        if not task:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Task not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskSerializer(task)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=TaskSerializer,
        responses={200: TaskSerializer},
        summary="Update Task Details",
        description="Update title, description, or priority. Direct status modifications are blocked; status must be transitioned using POST /api/v1/tasks/{id}/transition/."
    )
    def patch(self, request, pk: int, *args, **kwargs):
        task = self.get_object(pk)
        if not task:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Task not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        if 'status' in request.data:
            return Response({
                "success": False,
                "error": {
                    "code": "InvalidOperation",
                    "message": "Task status cannot be updated via PATCH. Use POST /api/v1/tasks/{id}/transition/ instead.",
                    "details": {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if 'title' in serializer.validated_data:
            task.title = serializer.validated_data['title']
        if 'description' in serializer.validated_data:
            task.description = serializer.validated_data['description']
        if 'priority' in serializer.validated_data:
            task.priority = serializer.validated_data['priority']
        task.save()

        ActivityLog.objects.create(
            project=task.project,
            task=task,
            actor=request.user,
            action=ActivityAction.TASK_UPDATED,
            metadata={'task_key': task.task_key}
        )

        task_data = TaskSerializer(TaskSelector.get_task_by_id(task.id, request.user)).data
        return Response({
            "success": True,
            "message": "Task details updated successfully.",
            "data": task_data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Soft-Delete Task",
        description="Soft-delete a task from the project."
    )
    def delete(self, request, pk: int, *args, **kwargs):
        task = self.get_object(pk)
        if not task:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Task not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        task.is_deleted = True
        task.deleted_at = timezone.now()
        task.save()

        return Response({
            "success": True,
            "message": "Task deleted successfully."
        }, status=status.HTTP_200_OK)
