from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for logging out and blacklisting refresh token.
    """
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
        except TokenError as e:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        return value
