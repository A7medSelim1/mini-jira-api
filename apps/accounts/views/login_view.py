from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from apps.accounts.serializers import UserSerializer
from apps.accounts.models import User


class LoginView(TokenObtainPairView):
    """
    Public endpoint for JWT user login.
    Returns access and refresh tokens along with basic user profile.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=request.data.get('email', '').strip().lower())
            user_data = UserSerializer(user).data
            response.data = {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "user": user_data,
                    "tokens": response.data
                }
            }
        return response
