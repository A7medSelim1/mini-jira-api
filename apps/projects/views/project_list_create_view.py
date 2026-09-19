from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer, ProjectCreateSerializer
from apps.projects.selectors import ProjectSelector
from apps.projects.services import ProjectService
from apps.projects.filters import ProjectFilter
from apps.utils.pagination import StandardResultsSetPagination


class ProjectListCreateView(APIView, StandardResultsSetPagination):
    """
    GET /api/v1/projects/ - List projects accessible to the current user (with search, ordering, pagination).
    POST /api/v1/projects/ - Create a new project (caller becomes reporter).
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProjectSerializer
    queryset = Project.objects.none()
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = ProjectFilter
    ordering_fields = ('created_at', 'title', 'key')
    ordering = ('-created_at',)

    def get_queryset(self, request):
        return ProjectSelector.get_user_projects(user=request.user)

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    @extend_schema(
        responses={200: ProjectSerializer(many=True)},
        summary="List Accessible Projects",
        description="Fetch all projects the authenticated user can access (as reporter or team member)."
    )
    def get(self, request, *args, **kwargs):
        base_queryset = self.get_queryset(request)
        filtered_queryset = self.filter_queryset(base_queryset)

        page = self.paginate_queryset(filtered_queryset, request, view=self)
        if page is not None:
            serializer = ProjectSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProjectSerializer(filtered_queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=ProjectCreateSerializer,
        responses={201: ProjectSerializer},
        summary="Create Project",
        description="Create a new project. Current authenticated user automatically becomes the project reporter."
    )
    def post(self, request, *args, **kwargs):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = ProjectService.create_project(
                key=serializer.validated_data['key'],
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                reporter=request.user
            )
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Project creation failed.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        project_data = ProjectSerializer(ProjectSelector.get_project_by_id(project.id, request.user)).data

        return Response({
            "success": True,
            "message": "Project created successfully.",
            "data": project_data
        }, status=status.HTTP_201_CREATED)
