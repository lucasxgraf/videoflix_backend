from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT authentication that reads the access token from an HttpOnly cookie
    instead of the Authorization header.
    """

    def authenticate(self, request):
        """
        Validate the access_token cookie and return (user, token).
        Returns None if the cookie is missing or invalid/expired, leaving the
        request unauthenticated instead of failing it outright - this lets
        AllowAny views (e.g. register, login) still work with a stale cookie.
        """
        token = request.COOKIES.get('access_token')
        if not token:
            return None

        try:
            validated_token = self.get_validated_token(token)
        except (InvalidToken, TokenError):
            return None

        return self.get_user(validated_token), validated_token
