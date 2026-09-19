from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework import status


class RefreshView(TokenRefreshView):
    """
    Public endpoint for refreshing access token using refresh token.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            response.data = {
                "success": True,
                "message": "Token refreshed successfully.",
                "data": response.data
            }
        return response
