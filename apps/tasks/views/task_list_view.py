from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer
from apps.tasks.selectors import TaskSelector
from apps.tasks.filters import TaskFilter
from apps.utils.pagination import StandardResultsSetPagination


class GlobalTaskListView(APIView, StandardResultsSetPagination):
    """
    GET /api/v1/tasks/
    Global task listing endpoint accessible to authenticated users across all their projects.
    Supports filtering (project, assignee, status, priority, date range), search, ordering, and pagination.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TaskSerializer
    queryset = Task.objects.none()
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TaskFilter
    ordering_fields = ('created_at', 'updated_at', 'priority', 'title')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        return TaskSelector.get_user_tasks(request.user)

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    @extend_schema(
        responses={200: TaskSerializer(many=True)},
        summary="Global Task List",
        description="Fetch tasks across all accessible projects. Supports filtering, full-text search, safe ordering, and pagination."
    )
    def get(self, request, *args, **kwargs):
        base_queryset = self.get_queryset(request)
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
