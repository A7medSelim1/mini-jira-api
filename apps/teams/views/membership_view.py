from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.teams.serializers import TeamMembershipSerializer
from apps.teams.selectors import TeamSelector
from apps.teams.services import TeamService
from apps.teams.permissions import IsTeamMember
from apps.accounts.models import User


class TeamMembershipListCreateView(APIView):
    """
    GET /api/v1/teams/{id}/members/ - List team members.
    POST /api/v1/teams/{id}/members/ - Add a member to the team.
    """
    permission_classes = (permissions.IsAuthenticated, IsTeamMember)
    serializer_class = TeamMembershipSerializer

    def get_team(self, team_id: int):
        team = TeamSelector.get_team_by_id(team_id)
        if not team:
            return None
        self.check_object_permissions(self.request, team)
        return team

    @extend_schema(
        responses={200: TeamMembershipSerializer(many=True)},
        summary="List Team Members",
        description="Fetch list of users enrolled in the team."
    )
    def get(self, request, pk: int, *args, **kwargs):
        team = self.get_team(pk)
        if not team:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Team not found.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        memberships = TeamSelector.get_team_members(team.id)
        serializer = TeamMembershipSerializer(memberships, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=TeamMembershipSerializer,
        responses={201: TeamMembershipSerializer},
        summary="Add Team Member",
        description="Add a user to the team using user_id or email."
    )
    def post(self, request, pk: int, *args, **kwargs):
        team = self.get_team(pk)
        if not team:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Team not found.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        user_id = request.data.get('user_id')
        email = request.data.get('email')

        target_user = None
        if user_id:
            target_user = User.objects.filter(id=user_id).first()
        elif email:
            target_user = User.objects.filter(email=email.strip().lower()).first()

        if not target_user:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "User not found. Provide a valid user_id or email.",
                    "details": {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            membership = TeamService.add_member(team=team, user=target_user)
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Failed to add member.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Member added successfully.",
            "data": TeamMembershipSerializer(membership).data
        }, status=status.HTTP_201_CREATED)


class TeamMembershipDetailView(APIView):
    """
    DELETE /api/v1/teams/{id}/members/{user_id}/ - Remove member from team.
    """
    permission_classes = (permissions.IsAuthenticated, IsTeamMember)
    serializer_class = TeamMembershipSerializer

    @extend_schema(
        summary="Remove Team Member",
        description="Remove a user from the specified team."
    )
    def delete(self, request, pk: int, user_id: int, *args, **kwargs):
        team = TeamSelector.get_team_by_id(pk)
        if not team:
            return Response({
                "success": False,
                "error": {
                    "code": "NotFound",
                    "message": "Team not found.",
                    "details": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, team)

        try:
            TeamService.remove_member(team=team, user_id=user_id)
        except ValidationError as e:
            return Response({
                "success": False,
                "error": {
                    "code": "ValidationError",
                    "message": "Failed to remove member.",
                    "details": e.message_dict if hasattr(e, 'message_dict') else str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Member removed successfully."
        }, status=status.HTTP_200_OK)
