from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.projects.serializers import ProjectSerializer
from apps.projects.selectors import ProjectSelector
from apps.projects.services import ProjectService
from apps.projects.permissions import HasProjectAccess, IsProjectReporter


class ProjectDetailView(APIView):
    """
    GET /api/v1/projects/{id}/ - Retrieve project detail.
    PATCH /api/v1/projects/{id}/ - Update project title/description (Reporter only).
    DELETE /api/v1/projects/{id}/ - Soft delete project (Reporter only).
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProjectSerializer

    def get_object(self, project_id: int):
        project = ProjectSelector.get_project_by_id(project_id, self.request.user)
        if not project:
            return None
        self.check_object_permissions(self.request, project)
        return project

    @extend_schema(
        responses={200: ProjectSerializer},
        summary="Retrieve Project Details",
        description="Fetch project information including assigned teams."
    )
    def get(self, request, pk: int, *args, **kwargs):
        self.permission_classes = (permissions.IsAuthenticated, HasProjectAccess)
        project = self.get_object(pk)
        if not project:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Project not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectSerializer(project)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=ProjectSerializer,
        responses={200: ProjectSerializer},
        summary="Update Project Settings",
        description="Update project title or description. Project Reporter permission required."
    )
    def patch(self, request, pk: int, *args, **kwargs):
        self.permission_classes = (permissions.IsAuthenticated, IsProjectReporter)
        project = self.get_object(pk)
        if not project:
            return Response({
                "success": False,
                "error": {
                    "code": "PermissionDenied",
                    "message": "Only the Project Reporter can update project settings.",
                    "details": {}
                }
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ProjectSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if 'title' in serializer.validated_data:
            project.title = serializer.validated_data['title']
        if 'description' in serializer.validated_data:
            project.description = serializer.validated_data['description']
        project.save()

        project_data = ProjectSerializer(ProjectSelector.get_project_by_id(project.id, request.user)).data
        return Response({
            "success": True,
            "message": "Project updated successfully.",
            "data": project_data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Archive / Soft-Delete Project",
        description="Soft-delete a project. Project Reporter permission required."
    )
    def delete(self, request, pk: int, *args, **kwargs):
        self.permission_classes = (permissions.IsAuthenticated, IsProjectReporter)
        project = self.get_object(pk)
        if not project:
            return Response({
                "success": False,
                "error": {
                    "code": "PermissionDenied",
                    "message": "Only the Project Reporter can delete the project.",
                    "details": {}
                }
            }, status=status.HTTP_403_FORBIDDEN)

        ProjectService.soft_delete_project(project, request.user)

        return Response({
            "success": True,
            "message": "Project deleted successfully."
        }, status=status.HTTP_200_OK)
