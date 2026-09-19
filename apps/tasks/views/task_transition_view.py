from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError, PermissionDenied
from drf_spectacular.utils import extend_schema

from apps.tasks.serializers import TaskSerializer, TaskTransitionSerializer
from apps.tasks.selectors import TaskSelector
from apps.tasks.services import TaskService
from apps.tasks.permissions import HasTaskAccess


class TaskTransitionView(APIView):
    """
    POST /api/v1/tasks/{id}/transition/
    Executes controlled task state machine transition.
    """
    permission_classes = (permissions.IsAuthenticated, HasTaskAccess)
    serializer_class = TaskTransitionSerializer

    @extend_schema(
        request=TaskTransitionSerializer,
        responses={200: TaskSerializer},
        summary="Transition Task Workflow Status",
        description="Executes a state machine transition (TODO -> IN_PROGRESS -> READY_FOR_REVIEW -> DONE / TODO). Role restrictions enforced per transition."
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

        self.check_object_permissions(request, task)

        serializer = TaskTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_status = serializer.validated_data['status']

        try:
            updated_task = TaskService.transition_task(
                task_id=task.id,
                target_status=target_status,
                actor=request.user
            )
        except PermissionDenied as e:
            return Response({
                "success": False,
                "error": {
                    "code": "PermissionDenied",
                    "message": str(e),
                    "details": {}
                }
            }, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Status transition failed.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        task_data = TaskSerializer(TaskSelector.get_task_by_id(updated_task.id, request.user)).data
        return Response({
            "success": True,
            "message": f"Task transitioned to {updated_task.status} successfully.",
            "data": task_data
        }, status=status.HTTP_200_OK)
