from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.projects.serializers import ProjectTeamSerializer
from apps.projects.selectors import ProjectSelector
from apps.projects.services import ProjectService
from apps.projects.permissions import IsProjectReporter
from apps.teams.models import Team


class ProjectTeamsListCreateView(APIView):
    """
    POST /api/v1/projects/{id}/teams/ - Assign a team to the project (Reporter only).
    """
    permission_classes = (permissions.IsAuthenticated, IsProjectReporter)
    serializer_class = ProjectTeamSerializer

    @extend_schema(
        request=ProjectTeamSerializer,
        responses={201: ProjectTeamSerializer},
        summary="Assign Team to Project",
        description="Assign a team to the specified project. Requires Project Reporter permissions."
    )
    def post(self, request, pk: int, *args, **kwargs):
        project = ProjectSelector.get_project_by_id(pk, request.user)
        if not project:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Project not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, project)

        serializer = ProjectTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        team = Team.objects.get(id=serializer.validated_data['team_id'])

        try:
            assignment = ProjectService.assign_team(project=project, team=team, actor=request.user)
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Failed to assign team to project.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Team assigned to project successfully.",
            "data": ProjectTeamSerializer(assignment).data
        }, status=status.HTTP_201_CREATED)


class ProjectTeamsDetailView(APIView):
    """
    DELETE /api/v1/projects/{id}/teams/{team_id}/ - Remove team from project (Reporter only).
    """
    permission_classes = (permissions.IsAuthenticated, IsProjectReporter)
    serializer_class = ProjectTeamSerializer

    @extend_schema(
        summary="Remove Team from Project",
        description="Remove a team assignment from a project. Requires Project Reporter permissions."
    )
    def delete(self, request, pk: int, team_id: int, *args, **kwargs):
        project = ProjectSelector.get_project_by_id(pk, request.user)
        if not project:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Project not found or access denied.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, project)

        try:
            ProjectService.remove_team(project=project, team_id=team_id, actor=request.user)
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Failed to remove team from project.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Team removed from project successfully."
        }, status=status.HTTP_200_OK)
