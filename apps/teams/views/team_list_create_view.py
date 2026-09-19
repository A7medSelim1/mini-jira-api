from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from apps.teams.serializers import TeamSerializer
from apps.teams.selectors import TeamSelector
from apps.teams.services import TeamService


class TeamListCreateView(APIView):
    """
    GET /api/v1/teams/ - List teams accessible to the current user.
    POST /api/v1/teams/ - Create a new team.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TeamSerializer

    @extend_schema(
        responses={200: TeamSerializer(many=True)},
        summary="List User Teams",
        description="Fetch all teams created by or assigned to the current user."
    )
    def get(self, request, *args, **kwargs):
        teams = TeamSelector.get_user_teams(user=request.user)
        serializer = TeamSerializer(teams, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=TeamSerializer,
        responses={201: TeamSerializer},
        summary="Create Team",
        description="Create a new team. Creator automatically becomes a member."
    )
    def post(self, request, *args, **kwargs):
        serializer = TeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            team = TeamService.create_team(
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                created_by=request.user
            )
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Team creation failed.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Re-fetch team with selector annotations
        team_data = TeamSerializer(TeamSelector.get_team_by_id(team.id)).data

        return Response({
            "success": True,
            "message": "Team created successfully.",
            "data": team_data
        }, status=status.HTTP_201_CREATED)
