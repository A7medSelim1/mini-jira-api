from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer, TaskCreateSerializer
from apps.tasks.selectors import TaskSelector
from apps.tasks.services import TaskService
from apps.tasks.filters import TaskFilter
from apps.projects.selectors import ProjectSelector
from apps.utils.pagination import StandardResultsSetPagination
from apps.accounts.models import User


class TaskListCreateView(APIView, StandardResultsSetPagination):
    """
    GET /api/v1/projects/{project_id}/tasks/ - List project tasks (with filtering, search, ordering, pagination).
    POST /api/v1/projects/{project_id}/tasks/ - Create a task in a project.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskSerializer
    queryset = Task.objects.none()
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TaskFilter
    ordering_fields = ('created_at', 'updated_at', 'priority', 'title')
    ordering = ('-created_at',)

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    @extend_schema(
        responses={200: TaskSerializer(many=True)},
        summary="List Project Tasks",
        description="Fetch tasks for a specific project. Supports filtering, text search, safe ordering, and pagination."
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

        base_queryset = TaskSelector.get_project_tasks(project.id, request.user)
        filtered_queryset = self.filter_queryset(base_queryset)

        page = self.paginate_queryset(filtered_queryset, request, view=self)
        if page is not None:
            serializer = TaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaskSerializer(filtered_queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=TaskCreateSerializer,
        responses={201: TaskSerializer},
        summary="Create Task",
        description="Create a new task in the project. Assignee must belong to an assigned team or be reporter."
    )
    def post(self, request, project_id: int, *args, **kwargs):
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

        serializer = TaskCreateSerializer(data=request.data, context={'project': project})
        serializer.is_valid(raise_exception=True)

        assignee_id = serializer.validated_data.get('assignee_id')
        assignee = User.objects.filter(id=assignee_id).first() if assignee_id else None

        try:
            task = TaskService.create_task(
                project=project,
                title=serializer.validated_data['title'],
                created_by=request.user,
                description=serializer.validated_data.get('description', ''),
                priority=serializer.validated_data.get('priority'),
                assignee=assignee
            )
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Task creation failed.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        task_data = TaskSerializer(TaskSelector.get_task_by_id(task.id, request.user)).data
        return Response({
            "success": True,
            "message": "Task created successfully.",
            "data": task_data
        }, status=status.HTTP_201_CREATED)
