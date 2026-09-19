from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from drf_spectacular.utils import extend_schema
from apps.accounts.serializers import LogoutSerializer


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the provided refresh token to securely log out the user.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LogoutSerializer

    @extend_schema(
        request=LogoutSerializer,
        summary="User Logout",
        description="Blacklists the provided refresh token to invalidate user session."
    )
    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
        except TokenError:
            return Response({
                "success": False,
                "error": {
                    "code": "InvalidToken",
                    "message": "Token is invalid or already blacklisted.",
                    "details": {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": "Successfully logged out."
        }, status=status.HTTP_200_OK)
