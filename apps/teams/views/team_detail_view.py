from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.teams.serializers import TeamSerializer
from apps.teams.selectors import TeamSelector
from apps.teams.services import TeamService
from apps.teams.permissions import IsTeamMember


class TeamDetailView(APIView):
    """
    GET /api/v1/teams/{id}/ - Retrieve team details.
    PATCH /api/v1/teams/{id}/ - Update team details.
    DELETE /api/v1/teams/{id}/ - Delete team.
    """
    permission_classes = (permissions.IsAuthenticated, IsTeamMember)
    serializer_class = TeamSerializer

    def get_object(self, team_id: int):
        team = TeamSelector.get_team_by_id(team_id)
        if not team:
            return None
        self.check_object_permissions(self.request, team)
        return team

    @extend_schema(
        responses={200: TeamSerializer},
        summary="Retrieve Team Details",
        description="Fetch detailed team information."
    )
    def get(self, request, pk: int, *args, **kwargs):
        team = self.get_object(pk)
        if not team:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Team not found.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TeamSerializer(team)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk: int, *args, **kwargs):
        team = self.get_object(pk)
        if not team:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Team not found.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TeamSerializer(team, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            updated_team = TeamService.update_team(
                team=team,
                name=serializer.validated_data.get('name'),
                description=serializer.validated_data.get('description')
            )
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Update failed.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        team_data = TeamSerializer(TeamSelector.get_team_by_id(updated_team.id)).data
        return Response({
            "success": True,
            "message": "Team updated successfully.",
            "data": team_data
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk: int, *args, **kwargs):
        team = self.get_object(pk)
        if not team:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Team not found.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        TeamService.delete_team(team)
        return Response({
            "success": True,
            "message": "Team deleted successfully."
        }, status=status.HTTP_200_OK)
