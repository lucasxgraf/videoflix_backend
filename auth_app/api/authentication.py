from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    JWT authentication that reads the access token from an HttpOnly cookie
    instead of the Authorization header.
    """

    def authenticate(self, request):
        """
        Validate the access_token cookie and return (user, token).
        Returns None if the cookie is missing, leaving the request unauthenticated.
        """
        token = request.COOKIES.get('access_token')
        if not token:
            return None

        validated_token = self.get_validated_token(token)
        return self.get_user(validated_token), validated_token
