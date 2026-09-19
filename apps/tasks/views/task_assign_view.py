from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.tasks.serializers import TaskSerializer, TaskAssignSerializer
from apps.tasks.selectors import TaskSelector
from apps.tasks.services import TaskService
from apps.projects.permissions import IsProjectReporter
from apps.accounts.models import User


class TaskAssignView(APIView):
    """
    POST /api/v1/tasks/{id}/assign/
    Assigns or unassigns a task to an eligible team member (Reporter only).
    """
    permission_classes = (permissions.IsAuthenticated, IsProjectReporter)
    serializer_class = TaskAssignSerializer

    @extend_schema(
        request=TaskAssignSerializer,
        responses={200: TaskSerializer},
        summary="Assign / Reassign Task",
        description="Assign task to an eligible user (must belong to a team assigned to the project). Project Reporter permission required."
    )
    def post(self, request, pk: int, *args, **kwargs):
        task = TaskSelector.get_task_by_id(pk, request.user)
        if not task:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Task not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # Check project reporter permission on task's project
        self.check_object_permissions(request, task.project)

        serializer = TaskAssignSerializer(data=request.data, context={'task': task})
        serializer.is_valid(raise_exception=True)

        assignee_id = serializer.validated_data.get('assignee_id')
        assignee = User.objects.filter(id=assignee_id).first() if assignee_id else None

        try:
            updated_task = TaskService.assign_task(
                task_id=task.id,
                assignee=assignee,
                actor=request.user
            )
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Task assignment failed.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        task_data = TaskSerializer(TaskSelector.get_task_by_id(updated_task.id, request.user)).data
        return Response({
            "success": True,
            "message": "Task assignment updated successfully.",
            "data": task_data
        }, status=status.HTTP_200_OK)
