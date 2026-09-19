from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from apps.accounts.serializers import UserSerializer
from apps.accounts.services import AuthService


class MeView(APIView):
    """
    Authenticated endpoint for viewing and updating current user profile.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    @extend_schema(
        responses={200: UserSerializer},
        summary="Retrieve Current Profile",
        description="Fetch authenticated user profile information."
    )
    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserSerializer,
        responses={200: UserSerializer},
        summary="Update Profile",
        description="Update profile fields (first_name, last_name) for current user."
    )
    def patch(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_user = AuthService.update_profile(
            user=request.user,
            first_name=serializer.validated_data.get('first_name'),
            last_name=serializer.validated_data.get('last_name')
        )
        
        return Response({
            "success": True,
            "message": "Profile updated successfully.",
            "data": UserSerializer(updated_user).data
        }, status=status.HTTP_200_OK)
