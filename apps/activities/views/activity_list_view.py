from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from apps.activities.serializers import ActivityLogSerializer
from apps.activities.selectors import ActivitySelector
from apps.projects.selectors import ProjectSelector
from apps.tasks.selectors import TaskSelector
from apps.utils.pagination import StandardResultsSetPagination


class ProjectActivityListView(APIView, StandardResultsSetPagination):
    """
    GET /api/v1/projects/{project_id}/activities/
    Lists immutable audit log history for a project (IDOR-protected, paginated).
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActivityLogSerializer

    @extend_schema(
        responses={200: ActivityLogSerializer(many=True)},
        summary="List Project Activity History",
        description="Fetch immutable audit log trail of events occurring within the project."
    )
    def get(self, request, project_id: int, *args, **kwargs):
        project = ProjectSelector.get_project_by_id(project_id, request.user)
        if not project:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Project not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        activities = ActivitySelector.get_project_activities(project.id, request.user)
        page = self.paginate_queryset(activities, request, view=self)
        if page is not None:
            serializer = ActivityLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ActivityLogSerializer(activities, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class TaskActivityListView(APIView, StandardResultsSetPagination):
    """
    GET /api/v1/tasks/{task_id}/activities/
    Lists immutable audit log history for a specific task (IDOR-protected, paginated).
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ActivityLogSerializer

    @extend_schema(
        responses={200: ActivityLogSerializer(many=True)},
        summary="List Task Activity History",
        description="Fetch immutable audit log trail of events for a specific task."
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

        activities = ActivitySelector.get_task_activities(task.id, request.user)
        page = self.paginate_queryset(activities, request, view=self)
        if page is not None:
            serializer = ActivityLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ActivityLogSerializer(activities, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
